"""Read-only per-instrument evidence gap overview; no promotion of trust.

Consumes existing audit results, never treats caller-provided True as attestation.
"""
FLAGS=("source_attested","instrument_segment_verified","segment_mic_verified",
       "broker_route_verified","degiro_fee_verified")
def summarize_spoor2_evidence(instruments, evidence):
    blocked={"status":"BLOCKED","trade_ready":False,"order_placement_enabled":False,
             "notify":False,"automatic_orders":False}
    if not isinstance(instruments,list) or not isinstance(evidence,dict):
        return {**blocked,"blocks":["INVALID_INPUT"],"rows":[]}
    rows=[]
    seen=set()
    for item in instruments:
        if not isinstance(item,dict) or not isinstance(item.get("isin"),str) or not item["isin"].strip():
            return {**blocked,"blocks":["INVALID_INSTRUMENT"],"rows":[]}
        isin=item["isin"]
        if isin in seen:
            return {**blocked,"blocks":["DUPLICATE_INSTRUMENT"],"rows":[]}
        seen.add(isin)
        audits=evidence.get(isin)
        if not isinstance(audits,dict):
            audits={}
        gaps=[]
        for flag in FLAGS:
            # Audit outputs are descriptive, not independent source verification.
            gaps.append({"gate":flag,"reported":audits.get(flag) is True,
                         "verified":False,"reason":"INDEPENDENT_ATTESTATION_NOT_ESTABLISHED"})
        audit_blocks=audits.get("blocks")
        if not isinstance(audit_blocks,list) or not all(isinstance(x,str) for x in audit_blocks):
            audit_blocks=["AUDIT_BLOCKS_MISSING_OR_INVALID"]
        rows.append({"isin":isin,"evidence_gaps":gaps,"audit_blocks":sorted(set(audit_blocks)),
                     "trade_ready":False})
    return {**blocked,"rows":sorted(rows,key=lambda x:x["isin"]),
            "blocks":["INDEPENDENT_EVIDENCE_NOT_VERIFIED"],
            "note":"Caller-provided audits cannot establish external authenticity or account-specific execution."}
