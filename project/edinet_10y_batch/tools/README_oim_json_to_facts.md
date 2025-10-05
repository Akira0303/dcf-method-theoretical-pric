# OIM JSON → facts.csv 変換ツール

Arelle の **Save Loadable OIM** が出力した `oim.json` を、フラットな `facts.csv` に変換します。

## 単体
python3 tools/oim_json_to_facts.py --in /path/to/oim.json --out /path/to/facts.csv

## 一括
bash tools/run_bulk_convert.sh /mnt/storage/project/edinet_10y_batch/work/oim_out

出力カラム: fact_id, concept, entity, period, unit, value, decimals, precision, lang, dimensions_json
