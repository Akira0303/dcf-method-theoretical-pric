
#!/usr/bin/env python3
# tools_api/prune_facts_csv.py
import sys, os, csv, argparse
from shutil import copyfile

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", required=True, help="Input facts_v2.csv")
    ap.add_argument("--out-min", dest="out_min", required=True, help="Output pruned CSV")
    ap.add_argument("--out-full", dest="out_full", required=True, help="Output full CSV (copy of input)")
    ap.add_argument("--keep", default="primary_clark,local_name,value,unit,entity.identifier,entity.scheme,periodStart,periodEnd,dimensions",
                    help="Comma-separated list of columns to keep for the pruned CSV")
    args = ap.parse_args()

    os.makedirs(os.path.dirname(args.out_full), exist_ok=True)
    copyfile(args.inp, args.out_full)

    keep = [c.strip() for c in args.keep.split(",") if c.strip()]

    try:
        csv.field_size_limit((1<<31)-1)
    except Exception:
        pass

    os.makedirs(os.path.dirname(args.out_min), exist_ok=True)
    with open(args.inp, encoding="utf-8") as f_in, open(args.out_min, "w", newline="", encoding="utf-8") as f_out:
        r = csv.DictReader(f_in)
        fields = [c for c in keep if (r.fieldnames and c in r.fieldnames)]
        w = csv.DictWriter(f_out, fieldnames=fields)
        w.writeheader()
        for row in r:
            w.writerow({k: row.get(k, "") for k in fields})

    print("OK", os.path.abspath(args.out_min), os.path.abspath(args.out_full))

if __name__ == "__main__":
    sys.exit(main())
