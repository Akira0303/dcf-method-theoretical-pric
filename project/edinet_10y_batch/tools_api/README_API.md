# tools_api - README
## 使い方
```bash
XBRL=/mnt/storage/project/edinet_10y_batch/work/unzipped/S1005Y57/XBRL/PublicDoc/*.xbrl
OUT=/mnt/storage/project/edinet_10y_batch/work/oim_out/S1005Y57/csv/facts.csv
/home/takagi/financial_report/bin/python tools_api/instance_to_oimcsv.py --xbrl "$XBRL" --out "$OUT"
wc -l "$OUT"
```
