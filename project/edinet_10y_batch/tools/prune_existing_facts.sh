
#!/usr/bin/env bash
# tools/prune_existing_facts.sh
set -euo pipefail
PY="${PY:-/home/takagi/financial_report/bin/python}"
OUTROOT="/mnt/storage/project/edinet_10y_batch/work/oim_out"
KEEP="${KEEP:-primary_clark,local_name,value,unit,entity.identifier,entity.scheme,periodStart,periodEnd,dimensions}"

find "$OUTROOT" -mindepth 2 -maxdepth 2 -type d -name csv | sort | while read -r cdir; do
  in="$cdir/facts_v2.csv"
  [ -s "$in" ] || { echo "SKIP: $cdir (no facts_v2.csv)"; continue; }
  min="$cdir/facts_v2.min.csv"
  full="$cdir/facts_v2.full.csv"
  log="${cdir%/csv}/prune.log"
  mkdir -p "$(dirname "$min")"
  {
    echo "IN=$in"
    "$PY" /mnt/storage/project/edinet_10y_batch/tools_api/prune_facts_csv.py \
      --in "$in" --out-min "$min" --out-full "$full" --keep "$KEEP"
    echo "MIN_SIZE=$(stat -c '%s' "$min") FULL_SIZE=$(stat -c '%s' "$full")"
  } > "$log" 2>&1
  echo "$(basename "$(dirname "$cdir")") OK $(stat -c '%s' "$min") $(stat -c '%s' "$full") $cdir"
done
