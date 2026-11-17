"""Offline research-only gate joining US route provenance to a fresh quote.

No network, credential access, notification, or order execution.
Self-declared evidence cannot authorize a trade.
"""
from datetime import datetime, timezone
from math import isfinite
from zoneinfo import ZoneInfo

NY = ZoneInfo("America/New_York")

def _instant(value):
    if not isinstance(value, str):
        return None
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return dt.astimezone(timezone.utc) if dt.tzinfo is not None else None
    except (ValueError, OverflowError):
        return None

def review_us_route_quote(route, quote, *, now, max_quote_age_seconds=120,
                          max_route_age_seconds=900):
    blocks = []
    if not isinstance(now, datetime) or now.tzinfo is None:
        raise ValueError("now must be an aware datetime")
    now = now.astimezone(timezone.utc)
    if not isinstance(route, dict):
        route = {}
        blocks.append("ROUTE_UNRESOLVED")
    if not isinstance(quote, dict):
        quote = {}
        blocks.append("QUOTE_UNRESOLVED")
    symbol = route.get("symbol")
    if not isinstance(symbol, str) or not symbol or symbol != quote.get("symbol"):
        blocks.append("SYMBOL_MISMATCH_OR_UNRESOLVED")
    rt = _instant(route.get("generated_utc"))
    qt = _instant(quote.get("provider_quote_utc"))
    if rt is None:
        blocks.append("ROUTE_TIME_UNRESOLVED")
    elif not 0 <= (now - rt).total_seconds() <= max_route_age_seconds:
        blocks.append("ROUTE_STALE_OR_FUTURE")
    if qt is None:
        blocks.append("QUOTE_TIME_UNRESOLVED")
    elif not -30 <= (now - qt).total_seconds() <= max_quote_age_seconds:
        blocks.append("QUOTE_STALE_OR_FUTURE")
    if rt is not None and qt is not None and qt < rt:
        blocks.append("QUOTE_PREDATES_ROUTE")
    last_bar = route.get("last_bar_date")
    if not isinstance(last_bar, str):
        blocks.append("ROUTE_BAR_DATE_UNRESOLVED")
    else:
        try:
            day = datetime.strptime(last_bar, "%Y-%m-%d").date()
            if qt is None or day != qt.astimezone(NY).date():
                blocks.append("ROUTE_BAR_SESSION_MISMATCH")
        except ValueError:
            blocks.append("ROUTE_BAR_DATE_UNRESOLVED")
    level = route.get("break_above_usd")
    zone = route.get("hold_zone_usd")
    price = quote.get("provider_quote")
    if (not isinstance(level, (int, float)) or isinstance(level, bool) or
            not isfinite(level) or level <= 0 or
            not isinstance(zone, (list, tuple)) or len(zone) != 2 or
            any(not isinstance(x, (int, float)) or isinstance(x, bool) or
                not isfinite(x) or x <= 0 for x in zone) or zone[0] > zone[1]):
        blocks.append("ROUTE_LEVELS_INVALID")
    if (not isinstance(price, (int, float)) or isinstance(price, bool) or
            not isfinite(price) or price <= 0):
        blocks.append("QUOTE_PRICE_INVALID")
    if route.get("phone_notification_eligible") is not True:
        blocks.append("PHONE_ROUTE_NOT_ELIGIBLE")
    if quote.get("provider_freshness_pass") is not True:
        blocks.append("PROVIDER_FRESHNESS_NOT_ATTESTED")
    if quote.get("intraday_hold_confirmed") is not True:
        blocks.append("INTRADAY_STRUCTURE_NOT_CONFIRMED")
    # Independent origin, exchange calendar, licensing, corporate actions and
    # broker execution evidence cannot be inferred from these two input objects.
    blocks += ["SOURCE_INDEPENDENCE_UNVERIFIED", "EXCHANGE_CALENDAR_UNVERIFIED",
               "DATA_LICENSE_UNVERIFIED", "CORPORATE_ACTIONS_UNVERIFIED",
               "BROKER_BID_ASK_UNVERIFIED", "NET_PROFIT_AND_RR_UNVERIFIED"]
    return {"status": "SHADOW_BLOCKED", "blocks": sorted(set(blocks)),
            "route_quote_temporally_consistent": not any(x in blocks for x in (
                "ROUTE_TIME_UNRESOLVED", "ROUTE_STALE_OR_FUTURE",
                "QUOTE_TIME_UNRESOLVED", "QUOTE_STALE_OR_FUTURE",
                "QUOTE_PREDATES_ROUTE", "ROUTE_BAR_DATE_UNRESOLVED",
                "ROUTE_BAR_SESSION_MISMATCH")),
            "trade_ready": False, "notify": False, "automatic_orders": False}
