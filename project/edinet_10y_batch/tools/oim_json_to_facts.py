#!/usr/bin/env python3
# oim_json_to_facts.py
# Usage: python oim_json_to_facts.py oim.json facts.csv
import sys, json, csv, os

def to_str(x):
    if x is None:
        return ""
    if isinstance(x, (int, float)):
        return str(x)
    if isinstance(x, (list, dict)):
        try:
            return json.dumps(x, ensure_ascii=False, separators=(",",":"))
        except Exception:
            return str(x)
    return str(x)

def main():
    if len(sys.argv) < 3:
        print("Usage: python oim_json_to_facts.py <oim.json> <facts.csv>", file=sys.stderr)
        sys.exit(2)
    ipath, opath = sys.argv[1], sys.argv[2]
    if not os.path.exists(ipath):
        print(f"[ERR] oim json not found: {ipath}", file=sys.stderr)
        sys.exit(3)
    with open(ipath, "r", encoding="utf-8") as f:
        d = json.load(f)

    # Try standard OIM JSON format ('facts' array)
    facts = d.get("facts")
    # Some exports may nest under 'document' or table-like structures; best effort
    if facts is None and isinstance(d, dict):
        for k in ("document","data","oim","instance"):
            v = d.get(k)
            if isinstance(v, dict) and "facts" in v:
                facts = v["facts"]
                break

    if not isinstance(facts, list):
        # Fallback: produce header only
        with open(opath, "w", encoding="utf-8", newline="") as wf:
            writer = csv.writer(wf)
            writer.writerow(["Name","Entity","Period","Unit","Dec","Prec","Lang","Value"])
        print("[WARN] no 'facts' array. wrote header only", file=sys.stderr)
        return

    # Write best-effort columns
    with open(opath, "w", encoding="utf-8", newline="") as wf:
        writer = csv.writer(wf)
        writer.writerow(["Name","Entity","Period","Unit","Dec","Prec","Lang","Value"])
        for fct in facts:
            if not isinstance(fct, dict):
                continue
            name = fct.get("concept") or fct.get("name") or ""
            ent  = fct.get("entity", "")
            per  = fct.get("period", "")
            unit = fct.get("unit", "")
            dec  = fct.get("decimals", "")
            prec = fct.get("precision", "")
            lang = fct.get("language", "") or fct.get("lang","")
            val  = fct.get("value") if "value" in fct else fct.get("v","")
            writer.writerow([to_str(name), to_str(ent), to_str(per), to_str(unit),
                             to_str(dec), to_str(prec), to_str(lang), to_str(val)])
    print("[OK] facts.csv created")

if __name__ == "__main__":
    main()
