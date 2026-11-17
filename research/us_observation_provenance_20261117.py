"""Research-only, offline provenance contract for US route observations.

Historical pivot origin is NOT the freshness timestamp of the discovery.
All evidence remains unverified; no live wiring or order/notification path.
"""
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

NY = ZoneInfo("America/New_York")

def _time(value):
    if not isinstance(value, str):
        return None
    try:
        t = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return t.astimezone(timezone.utc) if t.tzinfo else None
    except (ValueError, OverflowError):
        return None

def review_provenance(record, *, now, max_discovery_age_seconds=900,
                      max_intraday_age_seconds=900):
    if not isinstance(now, datetime) or now.tzinfo is None:
        raise ValueError("now must be timezone-aware")
    now = now.astimezone(timezone.utc)
    record = record if isinstance(record, dict) else {}
    fields = ("discovery_observed_utc", "source_daily_last_bar_utc",
              "source_intraday_last_bar_utc", "route_generated_utc",
              "quote_observed_utc")
    ts = {key: _time(record.get(key)) for key in fields}
    blocks = []
    for key, value in ts.items():
        if value is None:
            blocks.append(key.upper() + "_UNRESOLVED")
    discovery = ts["discovery_observed_utc"]
    intra = ts["source_intraday_last_bar_utc"]
    route = ts["route_generated_utc"]
    quote = ts["quote_observed_utc"]
    daily = ts["source_daily_last_bar_utc"]
    if discovery and not 0 <= (now-discovery).total_seconds() <= max_discovery_age_seconds:
        blocks.append("DISCOVERY_STALE_OR_FUTURE")
    if intra and not 0 <= (now-intra).total_seconds() <= max_intraday_age_seconds:
        blocks.append("INTRADAY_SOURCE_STALE_OR_FUTURE")
    if daily and discovery and daily > discovery:
        blocks.append("DAILY_BAR_AFTER_DISCOVERY")
    if intra and discovery and intra > discovery:
        blocks.append("INTRADAY_BAR_AFTER_DISCOVERY")
    if discovery and route and route < discovery:
        blocks.append("ROUTE_BEFORE_DISCOVERY")
    if route and quote and quote < route:
        blocks.append("QUOTE_BEFORE_ROUTE")
    if quote and quote > now:
        blocks.append("QUOTE_IN_FUTURE")
    session = record.get("exchange_session_date")
    pivot = record.get("pivot_origin_session_date")
    def valid_date(value):
        if not isinstance(value, str):
            return None
        try:
            d = datetime.strptime(value, "%Y-%m-%d").date()
            return d if d.isoformat() == value else None
        except ValueError:
            return None
    session_day = valid_date(session)
    pivot_day = valid_date(pivot)
    if session_day is None:
        blocks.append("EXCHANGE_SESSION_DATE_UNRESOLVED")
    if pivot_day is None:
        blocks.append("PIVOT_ORIGIN_DATE_UNRESOLVED")
    if session_day and quote and quote.astimezone(NY).date() != session_day:
        blocks.append("QUOTE_SESSION_MISMATCH")
    if pivot_day and session_day and pivot_day > session_day:
        blocks.append("PIVOT_FROM_FUTURE_SESSION")
    # A historic pivot may be older than the current quote. Age alone
    # cannot establish its validity or invalidate it.
    blocks += ["OFFICIAL_EXCHANGE_CALENDAR_UNVERIFIED",
               "PIVOT_CORPORATE_ACTION_VALIDITY_UNVERIFIED",
               "SOURCE_INDEPENDENCE_UNVERIFIED", "DATA_LICENSE_UNVERIFIED"]
    return {"status": "SHADOW_BLOCKED", "blocks": sorted(set(blocks)),
            "temporal_evidence_consistent": not any(b for b in blocks if b not in (
                "OFFICIAL_EXCHANGE_CALENDAR_UNVERIFIED",
                "PIVOT_CORPORATE_ACTION_VALIDITY_UNVERIFIED",
                "SOURCE_INDEPENDENCE_UNVERIFIED", "DATA_LICENSE_UNVERIFIED")),
            "trade_ready": False, "notify": False, "automatic_orders": False}
