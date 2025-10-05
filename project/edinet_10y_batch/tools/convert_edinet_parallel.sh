#!/usr/bin/env bash
# convert_edinet_parallel.sh (compat wrapper)
# Usage: bash convert_edinet_parallel.sh ZIP_ROOT OUT_ROOT
set -euo pipefail
ZIP_ROOT="${1:-/mnt/storage/project/edinet_10y_batch/work/zip}"
OUT_ROOT="${2:-/mnt/storage/project/edinet_10y_batch/work/oim_out}"

# This wrapper just delegates to the new robust bulk runner
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ -x "$SCRIPT_DIR/tools/bulk_ixds_to_facts.sh" ]; then
  bash "$SCRIPT_DIR/tools/bulk_ixds_to_facts.sh" "$ZIP_ROOT" "$OUT_ROOT"
else
  echo "[ERR] tools/bulk_ixds_to_facts.sh not found next to this script."
  echo "      Place this wrapper alongside the 'tools' folder from edinet_ixds_to_facts_toolkit."
  exit 2
fi
