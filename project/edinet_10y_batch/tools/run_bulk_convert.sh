#!/usr/bin/env bash
set -euo pipefail
BASE="${1:-/mnt/storage/project/edinet_10y_batch/work/oim_out}"
SELF_DIR="$(cd "$(dirname "$0")" && pwd)"
CONV="$SELF_DIR/oim_json_to_facts.py"

mapfile -d '' FILES < <(find "$BASE" -type f -name "oim.json" -print0)
for j in "${FILES[@]}"; do
  out="$(dirname "$j")/facts.csv"
  echo "[RUN] $j -> $out"
  python3 "$CONV" --in "$j" --out "$out" || echo "[WARN] failed: $j"
done
echo "[DONE]"
