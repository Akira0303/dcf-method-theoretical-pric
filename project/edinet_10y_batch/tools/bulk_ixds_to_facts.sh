#!/usr/bin/env bash
# bulk_ixds_to_facts.sh
# Purpose: ZIP(iXBRL set) -> extracted xBRL -> OIM CSV (facts.csv) with logs and a summary TSV.
# Env: Ubuntu 24.04, Python 3.12.3 venv 'financial_report', Arelle 2.37.61
# Req: PG not required here. Arelle CLI via `${ARELLE_PY} -m arelle.CntlrCmdLine`.
set -euo pipefail

ARELLE_PY="${ARELLE_PY:-python}"

ZIP_DIR="/mnt/storage/project/edinet_10y_batch/work/zip"
UNZ_DIR="/mnt/storage/project/edinet_10y_batch/work/unzipped"
OUT_ROOT="/mnt/storage/project/edinet_10y_batch/work/oim_out"
REPORT="${OUT_ROOT}/full_report.tsv"

# Header (idempotent-safe)
if [ ! -f "${REPORT}" ]; then
  echo -e "sid\tstatus\tfacts_lines\tmsg" > "${REPORT}"
fi

shopt -s nullglob
for z in "${ZIP_DIR}"/S*.zip; do
  sid="$(basename "${z}" .zip)"
  UNZ="${UNZ_DIR}/${sid}"
  OUT="${OUT_ROOT}/${sid}"
  OUTCSV="${OUT}/csv"
  LOG1="${OUT}/arelle_step1.log"
  LOG2="${OUT}/arelle_step2.log"
  mkdir -p "${UNZ}" "${OUT}" "${OUTCSV}"

  # Skip if facts.csv already exists and non-empty (>1 line)
  if [ -s "${OUTCSV}/facts.csv" ] && [ "$(wc -l < "${OUTCSV}/facts.csv")" -gt 1 ]; then
    echo -e "${sid}\tOK\t$(wc -l < "${OUTCSV}/facts.csv")\tSKIP(existing)" >> "${REPORT}"
    continue
  fi

  # Clean unzip dir to avoid stale
  rm -rf "${UNZ}"
  mkdir -p "${UNZ}"

  # Extract ZIP via Python (no external unzip dependency)
  python - "$z" "$UNZ" <<'PY'
import sys, zipfile, os
z, out = sys.argv[1], sys.argv[2]
with zipfile.ZipFile(z) as zf:
    zf.extractall(out)
PY

  # Step 1: inlineXbrlDocumentSet -> *_extracted.xbrl
  # Note: ixdsTarget="(default)" to consolidate a doc set if present
  ${ARELLE_PY} -m arelle.CntlrCmdLine \
    --plugins inlineXbrlDocumentSet \
    --file "[{\"ixds\":[{\"file\":\"${UNZ}\"}], \"ixdsTarget\":\"(default)\"}]" \
    --saveInstance \
    --logFile "${LOG1}" || true

  # Find the extracted instance
  INST="$(find "${UNZ}" -type f -name '*_extracted.xbrl' | head -n1 || true)"
  if [ -z "${INST}" ]; then
    # Some EDINET sets may already contain a loadable instance; try to locate *.xbrl fallback
    INST="$(find "${UNZ}" -type f -name '*.xbrl' | head -n1 || true)"
  fi

  status=""
  msg=""
  lines="0"

  if [ -z "${INST}" ]; then
    status="ERROR"
    msg="no_xbrl_instance"
    echo -e "${sid}\t${status}\t${lines}\t${msg}" >> "${REPORT}"
    continue
  fi

  # Step 2: xBRL -> OIM CSV
  rm -f "${OUTCSV}/facts.csv"
  mkdir -p "${OUTCSV}"
  ${ARELLE_PY} -m arelle.CntlrCmdLine \
    --plugins saveLoadableOIM \
    --file "${INST}" \
    --saveLoadableOIM "${OUTCSV}" \
    --plugInArg saveLoadableOIM.oimFileType=CSV \
    --logFile "${LOG2}" || true

  # Evaluate results
  if [ -s "${OUTCSV}/facts.csv" ]; then
    lines="$(wc -l < "${OUTCSV}/facts.csv")"
    # Check for errors in logs even if file exists
    if grep -iE 'error|fatal|exception' "${LOG2}" >/dev/null 2>&1; then
      status="ERROR"
      msg="errors_in_step2_log"
    else
      if [ "${lines}" -gt 1 ]; then
        status="OK"
        msg=""
      else
        status="HEADONLY"
        msg="facts_header_only"
      fi
    fi
  else
    # missing csv
    if grep -iE 'error|fatal|exception' "${LOG2}" >/dev/null 2>&1; then
      status="ERROR"
      msg="no_csv_with_errors"
    else
      status="NO_CSV"
      msg="no_csv_no_errors"
    fi
  fi

  echo -e "${sid}\t${status}\t${lines}\t${msg}" >> "${REPORT}"
done

echo "Done."
