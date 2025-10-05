#!/usr/bin/env python3
# tools_api/instance_to_oimcsv_v2.py
import sys, os, argparse, csv, json
from arelle import Cntlr
def qname_parts(q):
    try:
        uri = q.namespaceURI; ln = q.localName; pref = getattr(q, "prefix", "")
        clark = "{%s}%s" % (uri, ln) if uri else ln
        return pref, uri, ln, clark
    except Exception:
        s = str(q)
        if s.startswith("{"):
            uri, ln = s[1:].split("}",1); return "", uri, ln, s
        return "", "", s, s
def unit_str(u):
    if u is None: return ""
    try:
        nums = ["%s:%s"%(m.prefix,m.localName) for m in u.measures[0]] if u.measures and len(u.measures)>0 else []
        dens = ["%s:%s"%(m.prefix,m.localName) for m in u.measures[1]] if u.measures and len(u.measures)>1 else []
        return (" * ".join(nums))+((" / "+" * ".join(dens)) if dens else "")
    except Exception: return str(u) if u is not None else ""
def ctx_dates(ctx):
    if ctx is None: return ("","")
    try:
        if getattr(ctx,"isInstantPeriod",False):
            d = getattr(ctx,"endDatetime",None) or getattr(ctx,"instantDatetime",None)
            return ("", d.strftime("%Y-%m-%d") if d else "")
        s = ctx.startDatetime.strftime("%Y-%m-%d") if getattr(ctx,"startDatetime",None) else ""
        e = ctx.endDatetime.strftime("%Y-%m-%d") if getattr(ctx,"endDatetime",None) else ""
        return (s,e)
    except Exception: return ("","")
def dims_json(ctx):
    if ctx is None: return ""
    d={}
    try:
        for dimQn, mem in (getattr(ctx,"qnameDims",{}) or {}).items():
            dk = "{%s}%s"%(dimQn.namespaceURI, dimQn.localName)
            if hasattr(mem,'memberQname') and mem.memberQname is not None:
                vqn = mem.memberQname; d[dk] = "{%s}%s"%(vqn.namespaceURI, vqn.localName)
            elif hasattr(mem,'typedMember') and getattr(mem,'typedMember',None) is not None:
                d[dk] = str(getattr(mem.typedMember,"stringValue",""))
            else:
                vqn = getattr(mem,'qname',None); d[dk] = "{%s}%s"%(vqn.namespaceURI, vqn.localName) if vqn else str(mem)
    except Exception: pass
    return json.dumps(d, ensure_ascii=False)
def export_csv(xbrl_path, out_csv):
    ctrl = Cntlr.Cntlr(logFileName='logToPrint')
    try:
        model = ctrl.modelManager.load(xbrl_path)
        if model is None:
            print("ERROR: failed to load XBRL instance", file=sys.stderr); return 2
        os.makedirs(os.path.dirname(out_csv), exist_ok=True)
        with open(out_csv,"w",newline="",encoding="utf-8") as f:
            w=csv.writer(f); w.writerow(["id","primary","primary_clark","ns_uri","local_name","value","unit","decimals","precision","entity.identifier","entity.scheme","periodStart","periodEnd","lang","dimensions"])
            for i,fact in enumerate(getattr(model,"facts",[]), start=1):
                try:
                    qn = getattr(fact,"qname",None) or getattr(getattr(fact,"concept",None),"qname",None)
                    pref, uri, ln, clark = qname_parts(qn) if qn is not None else ("","","","")
                    value=getattr(fact,"value",""); unit=unit_str(getattr(fact,"unit",None))
                    decimals=getattr(fact,"decimals","") or ""; precision=getattr(fact,"precision","") or ""
                    ctx=getattr(fact,"context",None); ent_id=""; ent_scheme=""
                    ent_ident=getattr(ctx,"entityIdentifier",None) if ctx is not None else None
                    if ent_ident:
                        try: ent_scheme, ent_id = ent_ident
                        except Exception:
                            ent_scheme = getattr(ent_ident,"scheme","") or ""; ent_id = getattr(ent_ident,"identifier","") or ""
                    ps,pe=ctx_dates(ctx); lang=getattr(fact,"xmlLang","") or ""; dims=dims_json(ctx)
                    primary = (pref+":"+ln) if (pref and ln) else (ln or "")
                    w.writerow([i,primary,clark,uri,ln,value,unit,decimals,precision,ent_id,ent_scheme,ps,pe,lang,dims])
                except Exception: continue
        ctrl.modelManager.close(); ctrl.close(); return 0
    finally:
        try: ctrl.close()
        except Exception: pass
def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--xbrl",required=True); ap.add_argument("--out",required=True)
    a=ap.parse_args(); sys.exit(export_csv(a.xbrl,a.out))
if __name__=="__main__": main()
