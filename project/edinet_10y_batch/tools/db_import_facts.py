#!/usr/bin/env python3
import os, sys, argparse, csv, json
import psycopg2, psycopg2.extras
_max = sys.maxsize
while True:
    try:
        csv.field_size_limit(_max); break
    except OverflowError:
        _max = int(_max/10)
def ensure_table(conn):
    with conn.cursor() as cur:
        cur.execute("CREATE TABLE IF NOT EXISTS xbrl_staging_raw (source_id TEXT NOT NULL, fact JSONB NOT NULL, loaded_at TIMESTAMPTZ NOT NULL DEFAULT now());")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_xsr_source ON xbrl_staging_raw(source_id);")
    conn.commit()
def load_csv_stream(conn, sid, path, batch_size=5000):
    total=0; batch=[]
    with open(path, newline='', encoding='utf-8') as f:
        rdr=csv.DictReader(f)
        for rec in rdr:
            batch.append((sid, json.dumps(rec, ensure_ascii=False)))
            if len(batch)>=batch_size:
                with conn.cursor() as cur:
                    psycopg2.extras.execute_values(cur,"INSERT INTO xbrl_staging_raw (source_id, fact) VALUES %s", batch, template="(%s,%s)")
                conn.commit(); total+=len(batch); batch.clear()
        if batch:
            with conn.cursor() as cur:
                psycopg2.extras.execute_values(cur,"INSERT INTO xbrl_staging_raw (source_id, fact) VALUES %s", batch, template="(%s,%s)")
            conn.commit(); total+=len(batch)
    return total
def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--sid", required=True); ap.add_argument("--csv", required=True); ap.add_argument("--batch", type=int, default=int(os.environ.get("BATCH","5000"))); a=ap.parse_args()
    pgurl=os.environ.get("PGURL"); 
    if not pgurl: print("ERROR: PGURL not set", file=sys.stderr); sys.exit(2)
    conn=psycopg2.connect(pgurl)
    try:
        ensure_table(conn); n=load_csv_stream(conn, a.sid, a.csv, a.batch); print(f"loaded_rows={n}")
    finally:
        conn.close()
if __name__=="__main__": main()
