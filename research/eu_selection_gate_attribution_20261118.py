"""Offline EU gate-attribution audit; research only, no actual trade decisions.

Distinguishes proven failed setup criteria from unavailable verification.
No live data, retrospective outcomes, notifications or orders.
"""
from collections import Counter

GATES=("technical_structure","rr_min_2","net_profit_min_150","broker_quote",
       "event_clearance","portfolio_fit")
VALUES=("PASS","FAIL","UNKNOWN")

def audit_eu_gate_attribution(candidates):
    if not isinstance(candidates,list):
        return {"status":"INVALID_INPUT","blocks":["CANDIDATES_INVALID"],"trade_ready":False}
    counts=Counter()
    first_fail=Counter()
    all_fail=Counter()
    pending=Counter()
    invalid=[]
    seen=set()
    for index,c in enumerate(candidates):
        if not isinstance(c,dict) or not isinstance(c.get("id"),str) or not c["id"].strip() or c["id"] in seen or not isinstance(c.get("gates"),dict):
            invalid.append(index)
            continue
        seen.add(c["id"])
        gates=c["gates"]
        if any(k not in GATES or v not in VALUES for k,v in gates.items()):
            invalid.append(index)
            continue
        counts["valid_candidates"]+=1
        failures=[k for k in GATES if gates.get(k)=="FAIL"]
        unknown=[k for k in GATES if gates.get(k,"UNKNOWN")=="UNKNOWN"]
        if failures:
            counts["proven_gate_failure"]+=1
            first_fail[failures[0]]+=1
            all_fail.update(failures)
        elif unknown:
            counts["pending_verification"]+=1
        else:
            counts["all_declared_gates_passed_unverified"]+=1
        pending.update(unknown)
    return {"status":"RESEARCH_ONLY","candidate_count":len(candidates),
            "counts":dict(sorted(counts.items())),
            "first_failure_by_declared_gate_order":dict(sorted(first_fail.items())),
            "all_failure_frequency":dict(sorted(all_fail.items())),
            "missing_evidence_frequency":dict(sorted(pending.items())),
            "invalid_row_indices":invalid,
            "limitations":["Gate order is analytical, not proof of actual historical first rejection",
                           "PASS values are self-declared and not independent broker evidence",
                           "No inference of missed profits or trade readiness"],
            "trade_ready":False,"notify":False,"automatic_orders":False}
