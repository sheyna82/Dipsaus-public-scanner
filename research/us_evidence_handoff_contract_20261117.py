"""Offline-only US evidence envelope: preserve provenance without inventing it.

Pure transform for a future reviewed integration. Does not alter existing
discovery, handoff, routes, notifications, or order paths.
"""
from datetime import datetime, timezone

FIELDS=("discovery_observed_utc","source_daily_last_bar_utc",
        "source_intraday_last_bar_utc","pivot_origin_session_date",
        "exchange_session_date")

def _aware(value):
    if not isinstance(value,str):return False
    try:
        d=datetime.fromisoformat(value.replace("Z","+00:00"))
        return d.tzinfo is not None
    except ValueError:
        return False

def carry_evidence(discovery, handoff, *, symbol):
    if not isinstance(discovery,dict) or not isinstance(handoff,dict):
        return {"status":"BLOCKED","blocks":["INPUT_INVALID"],"evidence":{},
                "trade_ready":False,"notify":False,"automatic_orders":False}
    blocks=[]
    if not isinstance(symbol,str) or not symbol or discovery.get("symbol")!=symbol or handoff.get("symbol")!=symbol:
        blocks.append("SYMBOL_MISMATCH")
    evidence={}
    for field in FIELDS:
        source=discovery.get(field)
        forwarded=handoff.get(field)
        if source is None:
            blocks.append(field.upper()+"_SOURCE_MISSING")
        elif field.endswith("_utc") and not _aware(source):
            blocks.append(field.upper()+"_SOURCE_INVALID")
        elif forwarded is not None and forwarded!=source:
            blocks.append(field.upper()+"_HANDOFF_CONFLICT")
        else:
            evidence[field]=source
    return {"status":"SHADOW_BLOCKED","blocks":sorted(set(blocks+[
                "INDEPENDENT_SOURCE_UNVERIFIED","BROKER_EXECUTION_UNVERIFIED"])),
            "evidence":evidence,"provenance_fields_complete":len(evidence)==len(FIELDS) and not blocks,
            "trade_ready":False,"notify":False,"automatic_orders":False}
