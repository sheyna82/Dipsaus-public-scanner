"""EU forward-only research protocol. Immutable decisions before outcomes."""
from datetime import date
import hashlib
import json

SCHEMA="dipsaus_eu_prospective_v1"
MIN_CALENDAR_DAYS=180
MIN_SELECTED=30
MIN_REJECTED=30

def canonical_digest(payload):
    return hashlib.sha256(json.dumps(payload,sort_keys=True,separators=(",",":"),allow_nan=False).encode()).hexdigest()

def register_candidate(*,symbol,decision_day,pattern,selected,decision_cutoff,
                       features,source_sha256,benchmark_identity_verified=False):
    if benchmark_identity_verified is not True:
        raise ValueError("BENCHMARK_IDENTITY_UNVERIFIED")
    if type(selected) is not bool:raise ValueError("INVALID_SELECTION")
    if not isinstance(symbol,str) or not symbol.strip() or not isinstance(pattern,str) or not pattern.strip():
        raise ValueError("INVALID_IDENTIFIER")
    if not isinstance(source_sha256,str) or len(source_sha256)!=64 or any(c not in "0123456789abcdef" for c in source_sha256):
        raise ValueError("INVALID_SOURCE_HASH")
    d=date.fromisoformat(decision_day)
    cutoff=date.fromisoformat(decision_cutoff)
    if d>cutoff:raise ValueError("DECISION_AFTER_CUTOFF")
    if not isinstance(features,dict) or not features:raise ValueError("MISSING_FEATURES")
    if any(k.startswith("future_") or k in ("outcome","forward_return","exit_price") for k in features):
        raise ValueError("LOOKAHEAD_FEATURE")
    entry={"schema":SCHEMA,"symbol":symbol,"decision_day":d.isoformat(),
           "pattern":pattern,"selected":selected,"features":features,
           "source_sha256":source_sha256,"research_only":True,
           "trade_ready":False,"benchmark_identity_verified":True}
    entry["decision_sha256"]=canonical_digest(entry)
    return entry

def evaluate_readiness(entries,*,start_day,end_day):
    start=date.fromisoformat(start_day);end=date.fromisoformat(end_day)
    if end<start:raise ValueError("INVALID_PERIOD")
    days=(end-start).days
    counts={}
    seen=set()
    for e in entries:
        if e.get("schema")!=SCHEMA or e.get("research_only") is not True or e.get("trade_ready") is not False:
            raise ValueError("INVALID_ENTRY")
        digest=e.get("decision_sha256")
        if not isinstance(digest,str) or canonical_digest({k:v for k,v in e.items() if k!="decision_sha256"})!=digest:
            raise ValueError("DECISION_TAMPERED")
        d=date.fromisoformat(e["decision_day"])
        if not start<=d<=end:raise ValueError("OUTSIDE_WINDOW")
        key=(e["symbol"],e["pattern"],e["decision_day"])
        if key in seen:raise ValueError("DUPLICATE_DECISION")
        seen.add(key)
        c=counts.setdefault(e["pattern"],{"selected":0,"rejected":0})
        c["selected" if e["selected"] else "rejected"]+=1
    passed=days>=MIN_CALENDAR_DAYS and bool(counts) and all(
        c["selected"]>=MIN_SELECTED and c["rejected"]>=MIN_REJECTED for c in counts.values())
    return {"schema":SCHEMA,"research_only":True,"trade_ready":False,
            "minimum_observation_met":passed,"calendar_days":days,
            "counts":counts,"thresholds":{"days":MIN_CALENDAR_DAYS,
                      "selected_per_pattern":MIN_SELECTED,
                      "rejected_per_pattern":MIN_REJECTED}}
