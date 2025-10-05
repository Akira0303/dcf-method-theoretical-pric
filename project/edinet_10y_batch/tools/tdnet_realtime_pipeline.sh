#!/usr/bin/env bash
# tdnet_realtime_pipeline.sh
# Purpose: Process today's TDnet inbox S*.zip -> OIM CSV -> DB import -> DCF.
set -euo pipefail

ARELLE_PY="${ARELLE_PY:-python}"

INBOX="${1:-/mnt/storage/project/edinet_10y_batch/work/zip_inbox}"
ZIP_DIR="/mnt/storage/project/edinet_10y_batch/work/zip"
UNZ_DIR="/mnt/storage/project/edinet_10y_batch/work/unzipped"
OUT_ROOT="/mnt/storage/project/edinet_10y_batch/work/oim_out"

if [ -z "${PGURL:-}" ]; then
  echo "ERROR: PGURL is not set" >&2
  exit 2
fi

mkdir -p "${INBOX}" "${ZIP_DIR}" "${UNZ_DIR}" "${OUT_ROOT}"

# Move new zips to canonical location (do not overwrite existing)
shopt -s nullglob
for f in "${INBOX}"/S*.zip; do
  base="$(basename "$f")"
  dest="${ZIP_DIR}/${base}"
  if [ ! -f "${dest}" ]; then
    mv "$f" "${dest}"
    echo "moved ${base}"
  fi
done

# Run bulk conversion (will skip already-processed items)
"$(dirname "$0")/bulk_ixds_to_facts.sh"

# Import to DB and run DCF for items processed today (status OK)
REPORT="${OUT_ROOT}/full_report.tsv"
today="$(date +%Y-%m-%d)"
# Get list of SIDs with OK today (tail for speed; not required)
awk -v today="${today}" -F'\t' 'FNR>1 && $2=="OK" {print $1}' "${REPORT}" | sort -u | while read -r sid; do
  CSV_PATH="${OUT_ROOT}/${sid}/csv/facts.csv"
  if [ -s "${CSV_PATH}" ]; then
    PGURL="${PGURL}" "${ARELLE_PY}" "$(dirname "$0")/db_import_facts.py" --sid "${sid}" --csv "${CSV_PATH}"
    PGURL="${PGURL}" "${ARELLE_PY}" "$(dirname "$0")/dcf_calc.py" --sid "${sid}"
  fi
done

echo "TDnet pipeline done."
