#!/usr/bin/env python3
import os, sys, argparse, json
import psycopg2, psycopg2.extras
OP_CANDIDATES=[
    "ifrs-full:OperatingProfitLoss","ifrs-full:ProfitLossFromOperatingActivities",
    "jppfs_cor:OperatingIncome","jppfs_cor:OperatingProfit","jppfs_cor:OperatingProfitLoss",
    "jpcrp_cor:OperatingIncomeSummaryOfBusinessResults",
]
def fetch_series(conn, sid):
    q = r"SELECT (fact->>'primary') AS primary,(fact->>'value')::numeric AS val, NULLIF(fact->>'periodEnd','') AS pend FROM xbrl_staging_raw WHERE source_id = %s AND (fact->>'value') ~ '^-?[0-9]+(\.[0-9]+)?$' AND (fact->>'primary') IS NOT NULL"
    series=[]
    with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
        cur.execute(q,(sid,))
        for r in cur.fetchall():
            if r['primary'] in OP_CANDIDATES:
                fy=int(r['pend'][:4]) if r['pend'] else None
                if fy: series.append((fy, float(r['val'])))
    by_fy={}
    for fy,v in series: by_fy[fy]=v
    return sorted(by_fy.items())[-5:]
def dcf_value(fcfs,wacc,g):
    pv=0.0
    for t,f in enumerate(fcfs, start=1): pv+= f/((1+wacc)**t)
    term = fcfs[-1]*(1+g)/(wacc-g) if wacc>g else 0.0
    pv += term/((1+wacc)**len(fcfs)); return pv
def upsert(conn, sid, base, bull, bear, wacc, g, note):
    with conn.cursor() as cur:
        cur.execute("CREATE TABLE IF NOT EXISTS dcf_result (id BIGSERIAL PRIMARY KEY, source_id TEXT NOT NULL, valuation_base NUMERIC, valuation_bull NUMERIC, valuation_bear NUMERIC, wacc NUMERIC, g NUMERIC, as_of TIMESTAMPTZ NOT NULL DEFAULT now(), notes TEXT);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_dcf_sid ON dcf_result(source_id);")
        cur.execute("INSERT INTO dcf_result (source_id, valuation_base, valuation_bull, valuation_bear, wacc, g, notes) VALUES (%s,%s,%s,%s,%s,%s,%s)", (sid,base,bull,bear,wacc,g,note))
    conn.commit()
def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--sid", required=True); a=ap.parse_args()
    pgurl=os.environ.get("PGURL"); 
    if not pgurl: print("ERROR: PGURL not set", file=sys.stderr); sys.exit(2)
    wacc=float(os.environ.get("WACC","0.08")); g=float(os.environ.get("G","0.015"))
    conn=psycopg2.connect(pgurl)
    try:
        series=fetch_series(conn, a.sid)
        if not series:
            upsert(conn, a.sid, None, None, None, wacc, g, "no_operating_profit_series"); print("WARN: no operating profit series"); return
        last_fy,last_op=series[-1]; nopat=last_op*0.7; fcf0=nopat*0.2
        growth=[0.03,0.025,0.02,0.017,0.015]; fcfs=[]; f=fcf0
        for gty in growth: f=f*(1+gty); fcfs.append(f)
        base=dcf_value(fcfs,wacc,g); bull=dcf_value([x*1.05 for x in fcfs], max(wacc-0.015,0.01), min(g+0.01, wacc-0.005)); bear=dcf_value([x*0.95 for x in fcfs], wacc+0.015, max(g-0.01,0.0))
        note=f"fy_series={series}; fcf0={fcf0:.2f}"; upsert(conn, a.sid, base, bull, bear, wacc, g, note)
        print(json.dumps({"sid":a.sid,"valuation_base":base}, ensure_ascii=False))
    finally: conn.close()
if __name__=="__main__": main()
