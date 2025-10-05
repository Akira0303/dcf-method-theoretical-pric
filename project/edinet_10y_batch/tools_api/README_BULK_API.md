# bulk_xbrl_to_facts_api.sh（API版）
- 入力: `/mnt/storage/project/edinet_10y_batch/work/zip/S*.zip`
- 出力: `/mnt/storage/project/edinet_10y_batch/work/oim_out/S*/csv/facts.csv`
- レポート: `/mnt/storage/project/edinet_10y_batch/work/oim_out/full_report.tsv`
- 依存: venv python (`ARELLE_PY`), tools_api/instance_to_oimcsv.py

## 実行例
```bash
export ARELLE_PY="/home/takagi/financial_report/bin/python"
chmod +x /mnt/storage/project/edinet_10y_batch/tools_api/bulk_xbrl_to_facts_api.sh
/mnt/storage/project/edinet_10y_batch/tools_api/bulk_xbrl_to_facts_api.sh S1005Y57 S1005Y5I S1005YD8
# 全件
/mnt/storage/project/edinet_10y_batch/tools_api/bulk_xbrl_to_facts_api.sh
```
