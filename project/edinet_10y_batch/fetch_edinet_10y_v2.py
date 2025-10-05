
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EDINET batch fetcher (v2) — FIXED: always passes ?type=2 (list) / ?type=1 (zip)
- targets: CSV header 'securities_code' (4桁/5桁/英字)
- 正規化: 4文字→末尾'0'で5桁に
- host  : default https://api.edinet-fsa.go.jp (推奨). 切替は --base で。
- auth  : EDINET_SUBSCRIPTION_KEY を Header('Subscription-Key','X-API-KEY') と
          Query('Subscription-Key') の両方に付与（どちらでも通るよう冗長化）
- filter: --forms (v2のformCode, 例 030000), --ordinances (例 010) は“任意”。
"""
import os, sys, csv, time, argparse, datetime as dt
from typing import List, Dict, Set, Optional
from urllib.parse import urlencode

DEFAULT_BASE = "https://api.edinet-fsa.go.jp/api/v2"  # 推奨
ALT_BASE     = "https://disclosure.edinet-fsa.go.jp/api/v2"  # 代替

def eprint(*a, **k): print(*a, file=sys.stderr, **k)

def normalize_seccode(code: str) -> str:
    if not code: return ""
    c = str(code).strip().upper()
    if len(c) == 4: return c + "0"
    if len(c) == 5: return c
    if len(c) < 5:  return c + ("0" * (5 - len(c)))
    return c[:5]

def read_targets(path: str) -> Set[str]:
    with open(path, newline="", encoding="utf-8-sig") as f:
        r = csv.DictReader(f)
        cols = [c.strip() for c in (r.fieldnames or [])]
        key = "securities_code" if "securities_code" in cols else ("secCode5" if "secCode5" in cols else cols[0])
        s: Set[str] = set()
        for row in r:
            raw = (row.get(key) or "").strip()
            if raw: s.add(normalize_seccode(raw))
    return s

def daterange(start: dt.date, end: dt.date):
    d = start
    while d <= end:
        yield d
        d += dt.timedelta(days=1)

def build_headers():
    key = os.getenv("EDINET_SUBSCRIPTION_KEY", "").strip()
    h = {"User-Agent": "edinet_10y_v2/1.2"}
    if key:
        h["Subscription-Key"] = key
        h["X-API-KEY"] = key
    return h, key

def list_documents_for_date(session, base: str, date_str: str, key_q: str, verbose=False):
    # 必ず ?type=2 を付ける
    params = {"date": date_str, "type": "2"}
    if key_q: params["Subscription-Key"] = key_q
    url = f"{base}/documents.json"
    if verbose:
        eprint(f"[GET] {url}?{urlencode(params)}")
    r = session.get(url, params=params, timeout=60)
    if r.status_code >= 400:
        eprint(f"[{date_str}] LIST ERROR {r.status_code}: {r.text[:200]}")
        r.raise_for_status()
    data = r.json()
    docs = data.get("results") or data.get("documents") or []
    return docs

def download_doc(session, base: str, docid: str, outdir: str, key_q: str, sleep_between=0.0, verbose=False):
    # 必ず ?type=1 を付ける
    params = {"type": "1"}
    if key_q: params["Subscription-Key"] = key_q
    url = f"{base}/documents/{docid}"
    if verbose:
        eprint(f"[GET] {url}?{urlencode(params)}")
    outpath = os.path.join(outdir, f"{docid}.zip")
    if os.path.exists(outpath) and os.path.getsize(outpath) > 0:
        return outpath
    with session.get(url, params=params, timeout=300, stream=True) as r:
        if r.status_code >= 400:
            eprint(f"[DL] {docid} ERROR {r.status_code}: {r.text[:200]}")
            r.raise_for_status()
        tmp = outpath + ".part"
        with open(tmp, "wb") as f:
            for chunk in r.iter_content(chunk_size=1024*128):
                if chunk: f.write(chunk)
        os.replace(tmp, outpath)
    if sleep_between > 0: time.sleep(sleep_between)
    return outpath

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--targets", required=True)
    ap.add_argument("--start", required=True)
    ap.add_argument("--end", required=True)
    ap.add_argument("--forms", default="", help="EDINET v2 formCode (ex 030000), comma-separated")
    ap.add_argument("--ordinances", default="", help="EDINET v2 ordinanceCode (ex 010), comma-separated")
    ap.add_argument("--outdir", default="zips")
    ap.add_argument("--sleep", type=float, default=0.5)
    ap.add_argument("--base", default=DEFAULT_BASE, help=f"API base ({DEFAULT_BASE} or {ALT_BASE})")
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args()

    seccodes = read_targets(args.targets)
    if not seccodes:
        eprint("No securities_code in targets."); sys.exit(2)
    forms = set(s.strip() for s in args.forms.split(",") if s.strip())
    ordin = set(s.strip() for s in args.ordinances.split(",") if s.strip())
    start = dt.datetime.strptime(args.start, "%Y-%m-%d").date()
    end   = dt.datetime.strptime(args.end, "%Y-%m-%d").date()
    os.makedirs(args.outdir, exist_ok=True)

    try:
        import requests
        sess = requests.Session()
    except Exception:
        eprint("Requires 'requests'. pip install requests"); sys.exit(3)

    headers, key = build_headers()
    sess.headers.update(headers)

    total_listed = total_matched = total_downloaded = 0
    for d in daterange(start, end):
        ds = d.strftime("%Y-%m-%d")
        try:
            docs = list_documents_for_date(sess, args.base, ds, key_q=key, verbose=args.verbose)
        except Exception as ex:
            eprint(f"[{ds}] list failed: {ex}")
            continue
        if args.verbose:
            eprint(f"[{ds}] listed={len(docs)}")
        if not docs: 
            continue
        total_listed += len(docs)

        # filter
        todays = []
        for x in docs:
            sc = str(x.get("secCode","")).upper()
            if sc not in seccodes:
                continue
            if forms and str(x.get("formCode","")) not in forms:
                continue
            if ordin and str(x.get("ordinanceCode","")) not in ordin:
                continue
            todays.append(x)
        if args.verbose:
            eprint(f"[{ds}] matched={len(todays)}")

        total_matched += len(todays)
        for doc in todays:
            docid = str(doc.get("docID") or doc.get("docId") or "")
            if not docid: 
                continue
            try:
                out = download_doc(sess, args.base, docid, args.outdir, key_q=key, sleep_between=args.sleep, verbose=args.verbose)
                if out: total_downloaded += 1
            except Exception as ex:
                eprint(f"[{ds}] download failed docID={docid}: {ex}")
                continue
        time.sleep(0.1)

    eprint(f"Done. listed={total_listed} matched={total_matched} downloaded={total_downloaded}")

if __name__ == "__main__":
    main()
