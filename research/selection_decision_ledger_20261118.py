"""Offline prospective candidate-decision ledger validation.

Does not backfill historical decisions or treat missing observations as failures.
Records are supplied in memory; no IO, notifications or trading.
"""
from datetime import datetime, timezone
from collections import Counter
from research.eu_selection_gate_attribution_20261118 import GATES, VALUES

def _timestamp(value):
    if not isinstance(value,str):return None
    try:
        d=datetime.fromisoformat(value.replace("Z","+00:00"))
        return d.astimezone(timezone.utc) if d.tzinfo else None
    except (ValueError,OverflowError):return None

def audit_decision_ledger(records):
    if not isinstance(records,list):
        return {"status":"INVALID_INPUT","blocks":["RECORDS_INVALID"],
                "trade_ready":False,"notify":False,"automatic_orders":False}
    invalid=[];seen=set();counts=Counter();first_failure=Counter();pending=Counter()
    for i,r in enumerate(records):
        if not isinstance(r,dict):
            invalid.append({"index":i,"reason":"ROW_INVALID"});continue
        market=r.get("market");symbol=r.get("symbol");stage=r.get("stage")
        decision=_timestamp(r.get("decision_observed_utc"))
        evidence=_timestamp(r.get("source_observed_utc"))
        gates=r.get("gates")
        key=(market,symbol,r.get("decision_observed_utc"),stage)
        reason=None
        if market not in ("EU","US") or not isinstance(symbol,str) or not symbol.strip() or not isinstance(stage,str) or not stage.strip():
            reason="IDENTITY_OR_STAGE_INVALID"
        elif decision is None or evidence is None or evidence>decision:
            reason="PROVENANCE_INVALID"
        elif not isinstance(gates,dict) or any(k not in GATES or v not in VALUES for k,v in gates.items()):
            reason="GATES_INVALID"
        elif key in seen:
            reason="DUPLICATE_DECISION"
        if reason:
            invalid.append({"index":i,"reason":reason});continue
        seen.add(key);counts["valid_decisions"]+=1
        fails=[g for g in GATES if gates.get(g)=="FAIL"]
        missing=[g for g in GATES if gates.get(g,"UNKNOWN")=="UNKNOWN"]
        if fails:
            counts["failed_declared_gate"]+=1
            first_failure[fails[0]]+=1
        elif missing:
            counts["verification_pending"]+=1
        else:
            counts["all_declared_pass_unverified"]+=1
        pending.update(missing)
    return {"status":"RESEARCH_ONLY","record_count":len(records),
            "counts":dict(sorted(counts.items())),
            "first_failure_in_analytical_order":dict(sorted(first_failure.items())),
            "missing_evidence_frequency":dict(sorted(pending.items())),
            "invalid_records":invalid,
            "limitations":["No historical first-rejection sequence unless stage and timestamp evidence are independently sourced",
                           "Source and decision timestamps are caller-supplied, not independently attested",
                           "No lookahead outcomes, broker fills or trade authorization"],
            "trade_ready":False,"notify":False,"automatic_orders":False}
