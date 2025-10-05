# tools quick start

## 仮想環境（venv）について
- Arelle実行やPythonスクリプトは**仮想環境 financial_report**で動かしてください。
- どのシェルスクリプトも `ARELLE_PY` を尊重します。venvのpythonを指定すると安全です:
  ```bash
  export ARELLE_PY="/path/to/venv/financial_report/bin/python"
  ```
- 指定が無い場合はPATH上の `python` を使用します。


## 固定パス・環境
- ZIP: `/mnt/storage/project/edinet_10y_batch/work/zip/S*.zip`
- 展開先: `/mnt/storage/project/edinet_10y_batch/work/unzipped/S*`
- 出力: `/mnt/storage/project/edinet_10y_batch/work/oim_out/S*/csv/facts.csv`
- ログ: `/mnt/storage/project/edinet_10y_batch/work/oim_out/S*/arelle_step*.log`
- 集計: `/mnt/storage/project/edinet_10y_batch/work/oim_out/full_report.tsv`
- DB: env `PGURL="postgresql://user:pass@host:5432/db"`

Arelle (plugins): `inlineXbrlDocumentSet`, `saveLoadableOIM` 有効。CLI: `python -m arelle.CntlrCmdLine`

## 単発検証（例）
```bash
# venv有効化は省略（financial_report）
UNZ=/mnt/storage/project/edinet_10y_batch/work/unzipped/S1005ZFE
OUT=/mnt/storage/project/edinet_10y_batch/work/oim_out/S1005ZFE
mkdir -p "$UNZ" "$OUT" "$OUT/csv"
# Step1: 抽出xBRL
python -m arelle.CntlrCmdLine --plugins inlineXbrlDocumentSet \
  --file '[{"ixds":[{"file":"'"$UNZ"'"}], "ixdsTarget":"(default)"}]' \
  --saveInstance --logFile "$OUT/arelle_step1.log"
# Step2: OIM-CSV
INST=$(find "$UNZ" -type f -name '*_extracted.xbrl' | head -n1)
python -m arelle.CntlrCmdLine --plugins saveLoadableOIM \
  --file "$INST" --saveLoadableOIM "$OUT/csv" \
  --plugInArg saveLoadableOIM.oimFileType=CSV \
  --logFile "$OUT/arelle_step2.log"
wc -l "$OUT/csv/facts.csv"
```

## バルク変換
```bash
chmod +x tools/bulk_ixds_to_facts.sh
tools/bulk_ixds_to_facts.sh
# 成果は full_report.tsv を確認
```

## DB取り込み & DCF
```bash
export PGURL="postgresql://user:pass@host:5432/db"
tools/db_import_facts.py --sid S1005ZFE --csv /mnt/storage/project/edinet_10y_batch/work/oim_out/S1005ZFE/csv/facts.csv
tools/dcf_calc.py --sid S1005ZFE
```

## TDnet 当日分パイプライン
```bash
export PGURL="postgresql://user:pass@host:5432/db"
chmod +x tools/tdnet_realtime_pipeline.sh
tools/tdnet_realtime_pipeline.sh /mnt/storage/project/edinet_10y_batch/work/tdnet_inbox
```

### cron（日次）
```
# 毎日 08:05 JST
5 8 * * * export PATH="$HOME/.pyenv/versions/3.12.3/bin:$PATH"; source /path/to/venv/financial_report/bin/activate; export PGURL='postgresql://user:pass@host:5432/db'; /path/to/tools/tdnet_realtime_pipeline.sh /mnt/storage/project/edinet_10y_batch/work/tdnet_inbox >> /mnt/storage/project/edinet_10y_batch/work/oim_out/cron.log 2>&1
```

## dcf_result 初回DDL
```bash
psql "$PGURL" -f tools/dcf_result.sql
```

## 失敗時の集計
- `status` は {OK, HEADONLY, NO_CSV, ERROR}
- `facts_lines` は行数（1ならヘッダのみ）
- `msg` は補足（無い場合は空）
