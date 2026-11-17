"""Offline-only US evidence envelope: preserve provenance without inventing it.

Pure transform for a future reviewed integration. Does not alter existing
discovery, handoff, routes, notifications, or order paths.
"""
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
NY = ZoneInfo('America/New_York')

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
    def parsed(name):
        value=evidence.get(name)
        return datetime.fromisoformat(value.replace("Z","+00:00")).astimezone(timezone.utc) if isinstance(value,str) and _aware(value) else None
    discovery_time=parsed("discovery_observed_utc")
    daily_time=parsed("source_daily_last_bar_utc")
    intraday_time=parsed("source_intraday_last_bar_utc")
    if daily_time and discovery_time and daily_time > discovery_time:
        blocks.append("DAILY_BAR_AFTER_DISCOVERY")
    if intraday_time and discovery_time and intraday_time > discovery_time:
        blocks.append("INTRADAY_BAR_AFTER_DISCOVERY")
    if daily_time and intraday_time and daily_time > intraday_time:
        blocks.append("DAILY_BAR_AFTER_INTRADAY_BAR")
    def date_value(name):
        value=evidence.get(name)
        if not isinstance(value,str):return None
        try:
            day=datetime.strptime(value,"%Y-%m-%d").date()
            return day if day.isoformat()==value else None
        except ValueError:return None
    session=date_value("exchange_session_date")
    pivot=date_value("pivot_origin_session_date")
    if "exchange_session_date" in evidence and session is None:
        blocks.append("EXCHANGE_SESSION_DATE_INVALID")
    if "pivot_origin_session_date" in evidence and pivot is None:
        blocks.append("PIVOT_ORIGIN_SESSION_DATE_INVALID")
    if session and intraday_time and intraday_time.astimezone(NY).date()!=session:
        blocks.append("INTRADAY_SESSION_MISMATCH")
    if pivot and session and pivot>session:
        blocks.append("PIVOT_FROM_FUTURE_SESSION")
    return {"status":"SHADOW_BLOCKED","blocks":sorted(set(blocks+[
                "INDEPENDENT_SOURCE_UNVERIFIED","BROKER_EXECUTION_UNVERIFIED"])),
            "evidence":evidence,"provenance_fields_complete":len(evidence)==len(FIELDS) and not blocks,
            "trade_ready":False,"notify":False,"automatic_orders":False}
