"""Research-only European relative strength with explicit benchmark provenance gate."""
from datetime import datetime,timezone
from zoneinfo import ZoneInfo
import math
import hashlib
import base64
import binascii
import json

PAIRS={"ASML.AS":"AEX","IFX.DE":"DAX_PRICE","NOKIA.HE":"OMXH25","RHM.DE":"DAX_PRICE"}
def session_day(bar,zone):
    return datetime.fromtimestamp(bar["t"],timezone.utc).astimezone(ZoneInfo(zone)).date().isoformat()
ZONES={"ASML.AS":"Europe/Amsterdam","IFX.DE":"Europe/Berlin","NOKIA.HE":"Europe/Helsinki","RHM.DE":"Europe/Berlin"}
BENCH_ZONES={"AEX":"Europe/Amsterdam","DAX_PRICE":"Europe/Berlin","OMXH25":"Europe/Helsinki","STOXX600_PRICE":"Europe/Paris"}
def compare(europe,benchmarks,identity_evidence,as_of_complete_day):
    # Explicitly supplied and frozen by caller; never silently assume a date.
    from datetime import date
    try:
        cutoff=date.fromisoformat(as_of_complete_day)
        if cutoff.isoformat()!=as_of_complete_day:raise ValueError()
    except (TypeError,ValueError):
        raise ValueError('INVALID_COMPLETE_SESSION_CUTOFF')
    if europe.get("trade_ready") is not False or benchmarks.get("trade_ready") is not False:
        raise ValueError("RESEARCH_ONLY_REQUIRED")
    if not identity_evidence or set(identity_evidence)!={"AEX","DAX_PRICE","OMXH25","STOXX600_PRICE"} or not all(identity_evidence.values()):
        raise ValueError("BENCHMARK_IDENTITY_UNVERIFIED")
    # A captured Helsinki label audit can veto comparison, regardless of caller identity flags.
    omx=benchmarks.get("series",{}).get("OMXH25",{})
    label_audit=omx.get("daily_label_audit")
    if label_audit is None:
        raise ValueError("OMXH25_DAILY_LABEL_AUDIT_MISSING")
    if label_audit is not None:
        if (not isinstance(label_audit,dict) or
            label_audit.get("validation_status")!="consistent_unverified" or
            label_audit.get("checked")!=len(omx.get("bars",[])) or
            label_audit.get("consistent")!=label_audit.get("checked") or
            label_audit.get("inconsistent_dates")!=[] or
            label_audit.get("identity_approved") is not False):
            raise ValueError("OMXH25_DAILY_LABEL_AUDIT_BLOCKED")
    # Provider metadata is a necessary provenance contract, not independent proof.
    metadata=omx.get("provider_metadata")
    if (not isinstance(metadata,dict) or
        metadata.get("symbol")!="^OMXH25" or
        metadata.get("currency")!="EUR" or
        metadata.get("instrumentType")!="INDEX" or
        not isinstance(metadata.get("longName"),str) or
        "Helsinki 25" not in metadata["longName"]):
        raise ValueError("OMXH25_PROVIDER_METADATA_UNVERIFIED")
    raw_digest=omx.get("source_sha256")
    if (not isinstance(raw_digest,str) or len(raw_digest)!=64 or
        any(ch not in "0123456789abcdef" for ch in raw_digest)):
        raise ValueError("OMXH25_SOURCE_DIGEST_MISSING")
    raw_b64=omx.get("source_raw_base64")
    if not isinstance(raw_b64,str) or not raw_b64:
        raise ValueError("OMXH25_RAW_SOURCE_MISSING")
    try:
        raw=base64.b64decode(raw_b64,validate=True)
    except (binascii.Error,ValueError) as exc:
        raise ValueError("OMXH25_RAW_SOURCE_INVALID") from exc
    if not raw or len(raw)>2000000 or hashlib.sha256(raw).hexdigest()!=raw_digest:
        raise ValueError("OMXH25_RAW_SOURCE_HASH_MISMATCH")
    # Audit digest must bind to the exact canonical daily bars used below.
    bars_digest=hashlib.sha256(json.dumps(omx["bars"],sort_keys=True,separators=(",",":"),allow_nan=False).encode()).hexdigest()
    if label_audit.get("bars_sha256")!=bars_digest:
        raise ValueError("OMXH25_DAILY_LABEL_AUDIT_HASH_MISMATCH")
    # Recompute from actual daily bars: stored audit flags alone are not evidence.
    from research_capture_europe_benchmarks import audit_omxh25_daily_bar
    try:
        recomputed=[audit_omxh25_daily_bar(b) for b in omx["bars"]]
    except (ValueError,OverflowError,TypeError,KeyError) as exc:
        raise ValueError("OMXH25_DAILY_LABEL_RECOMPUTE_FAILED") from exc
    expected_inconsistent=[a["session_date"] for a in recomputed if not a["session_open_label_consistent"]]
    expected_consistent=len(recomputed)-len(expected_inconsistent)
    if (label_audit["consistent"]!=expected_consistent or
        label_audit["inconsistent_dates"]!=expected_inconsistent):
        raise ValueError("OMXH25_DAILY_LABEL_AUDIT_CONTENT_MISMATCH")
    if (expected_inconsistent or
        len({a["session_date"] for a in recomputed})!=len(recomputed)):
        raise ValueError("OMXH25_DAILY_LABEL_RECOMPUTE_BLOCKED")
    result={}
    for stock,primary in PAIRS.items():
        stock_bars=europe["series"][stock]["bars"]
        stock_by_date={session_day(b,ZONES[stock]):b for b in stock_bars}
        if len(stock_by_date)!=len(stock_bars):raise ValueError("DUPLICATE_STOCK_SESSION")
        result[stock]={}
        for name in (primary,"STOXX600_PRICE"):
            index_bars=benchmarks["series"][name]["bars"]
            idx={session_day(b,BENCH_ZONES[name]):b for b in index_bars}
            if len(idx)!=len(index_bars):raise ValueError("DUPLICATE_BENCHMARK_SESSION")
            common=sorted(set(stock_by_date)&set(idx))
            # Never use current, potentially incomplete session. Explicitly choose
            # a fixed last complete day in the caller's research protocol.
            common=[d for d in common if d<=as_of_complete_day]
            if len(common)<21:raise ValueError("INSUFFICIENT_MATCHED_DAYS")
            last,prior=common[-1],common[-21]
            a=stock_by_date[last]["close"]/stock_by_date[prior]["close"]-1
            b=idx[last]["close"]/idx[prior]["close"]-1
            rs=100*(a-b)
            if not math.isfinite(rs):raise ValueError("NONFINITE")
            result[stock][name]={"last_complete_day":last,"prior_day":prior,"relative_strength_20d_pct":rs,
                                  "matched_sessions":len(common),"trade_ready":False}
    return {"schema":"dipsaus_eu_relative_strength_research_v1","research_only":True,"trade_ready":False,
            "selection_thresholds_approved":False,"comparisons":result}
