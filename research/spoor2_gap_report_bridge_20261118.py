"""Join existing Spoor 2 audit outputs into a research-only evidence gap overview.

Never promotes audit claims to independently verified source evidence.
"""
from research.spoor2_evidence_gap_overview_20261118 import summarize_spoor2_evidence

AUDIT_KEYS=("instrument","mic","xetra","degiro","fees","manifest")

def build_spoor2_gap_report(instruments, audits_by_isin):
    if not isinstance(instruments,list) or not isinstance(audits_by_isin,dict):
        return summarize_spoor2_evidence(instruments,audits_by_isin)
    combined={}
    for item in instruments:
        if not isinstance(item,dict) or not isinstance(item.get("isin"),str):
            continue
        isin=item["isin"]
        bundle=audits_by_isin.get(isin)
        if not isinstance(bundle,dict):
            combined[isin]={"blocks":["AUDIT_BUNDLE_MISSING"]}
            continue
        blocks=[]
        sources={}
        for key in AUDIT_KEYS:
            audit=bundle.get(key)
            if not isinstance(audit,dict):
                blocks.append(key.upper()+"_AUDIT_MISSING")
                sources[key]="MISSING"
                continue
            sources[key]="REPORTED_BLOCKED" if audit.get("status")=="BLOCKED" else "REPORTED_UNATTESTED"
            bs=audit.get("blocks")
            if isinstance(bs,list) and all(isinstance(x,str) for x in bs):
                blocks.extend(key.upper()+":"+x for x in bs)
            else:
                blocks.append(key.upper()+"_BLOCKS_MISSING")
        combined[isin]={"blocks":blocks}
    result=summarize_spoor2_evidence(instruments,combined)
    for row in result["rows"]:
        bundle=audits_by_isin.get(row["isin"])
        row["audit_sources"]={key:(
            "MISSING" if not isinstance(bundle,dict) or not isinstance(bundle.get(key),dict)
            else "REPORTED_BLOCKED" if bundle[key].get("status")=="BLOCKED"
            else "REPORTED_UNATTESTED"
        ) for key in AUDIT_KEYS}
    result["integration_status"]="RESEARCH_ONLY_UNATTESTED"
    return result
