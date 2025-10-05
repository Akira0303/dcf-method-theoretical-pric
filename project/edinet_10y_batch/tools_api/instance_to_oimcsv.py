#!/usr/bin/env python3
# instance_to_oimcsv.py (API版, warning-free)
import sys, os, argparse, csv, json
from arelle import Cntlr

def qname_str(q):
    try:
        return f"{q.prefix}:{q.localName}" if getattr(q, "prefix", None) else q.clarkNotation
    except Exception:
        return str(q)

def unit_str(u):
    if u is None:
        return ""
    try:
        nums = ["{0}:{1}".format(m.prefix, m.localName) for m in u.measures[0]] if u.measures and len(u.measures) > 0 else []
        dens = ["{0}:{1}".format(m.prefix, m.localName) for m in u.measures[1]] if u.measures and len(u.measures) > 1 else []
        if dens:
            return " * ".join(nums) + " / " + " * ".join(dens)
        return " * ".join(nums)
    except Exception:
        return str(u)

def ctx_dates(ctx):
    if ctx is None:
        return ("","")
    try:
        if getattr(ctx, "isInstantPeriod", False):
            d = getattr(ctx, "endDatetime", None) or getattr(ctx, "instantDatetime", None)
            return ("", d.strftime("%Y-%m-%d") if d else "")
        else:
            s = ctx.startDatetime.strftime("%Y-%m-%d") if getattr(ctx, "startDatetime", None) else ""
            e = ctx.endDatetime.strftime("%Y-%m-%d") if getattr(ctx, "endDatetime", None) else ""
            return (s, e)
    except Exception:
        return ("","")

def dims_json(ctx):
    if ctx is None:
        return ""
    d = {}
    qnameDims = getattr(ctx, "qnameDims", {}) or {}
    for dimQn, mem in qnameDims.items():
        dim = qname_str(dimQn)
        if hasattr(mem, 'memberQname'):
            d[dim] = qname_str(mem.memberQname)
        elif hasattr(mem, 'typedMember'):
            d[dim] = str(getattr(mem.typedMember, "stringValue", ""))
        else:
            d[dim] = qname_str(getattr(mem, 'qname', ""))
    return json.dumps(d, ensure_ascii=False)

def export_csv(xbrl_path, out_csv):
    ctrl = Cntlr.Cntlr(logFileName='logToPrint')
    try:
        model = ctrl.modelManager.load(xbrl_path)
        if model is None:
            print("ERROR: failed to load XBRL instance", file=sys.stderr)
            return 2
        os.makedirs(os.path.dirname(out_csv), exist_ok=True)
        with open(out_csv, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["id","primary","value","unit","decimals","precision","entity.identifier","entity.scheme","periodStart","periodEnd","lang","dimensions"])
            for i, fact in enumerate(getattr(model, "facts", []), start=1):
                try:
                    primary = qname_str(getattr(fact, "qname", getattr(getattr(fact, "concept", None), "qname", "")))
                    value = getattr(fact, "value", "")
                    unit = unit_str(getattr(fact, "unit", None))
                    decimals = getattr(fact, "decimals", "") or ""
                    precision = getattr(fact, "precision", "") or ""
                    ctx = getattr(fact, "context", None)
                    ent_id = ""; ent_scheme = ""
                    ent_ident = getattr(ctx, "entityIdentifier", None) if ctx is not None else None
                    if ent_ident is not None:
                        ent_scheme, ent_id = ent_ident or ("","")
                    ps, pe = ctx_dates(ctx)
                    lang = getattr(fact, "xmlLang", "") or ""
                    dims = dims_json(ctx)
                    w.writerow([i, primary, value, unit, decimals, precision, ent_id, ent_scheme, ps, pe, lang, dims])
                except Exception:
                    continue
        ctrl.modelManager.close()
        ctrl.close()
        return 0
    finally:
        try: ctrl.close()
        except Exception: pass

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--xbrl", required=True, help="Path to instance XBRL (*.xbrl)")
    ap.add_argument("--out", required=True, help="Output CSV path (facts.csv)")
    args = ap.parse_args()
    rc = export_csv(args.xbrl, args.out)
    sys.exit(rc)

if __name__ == "__main__":
    main()
