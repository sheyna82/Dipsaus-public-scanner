"""Research-only broker evidence intake; claims are never authentication."""
from datetime import datetime, timezone
import math

def assess_broker_evidence(payload, *, now_utc, max_age_hours=24):
    """Validate broker-snapshot envelope without claiming external verification."""
    if not isinstance(payload, dict):
        raise ValueError("INVALID_BROKER_EVIDENCE")
    if not isinstance(now_utc, datetime) or now_utc.tzinfo is None or now_utc.utcoffset() is None:
        raise ValueError("INVALID_NOW")
    if (not isinstance(max_age_hours, (int, float)) or isinstance(max_age_hours, bool)
            or not math.isfinite(max_age_hours) or max_age_hours <= 0):
        raise ValueError("INVALID_MAX_AGE")
    required = {"source", "account_scope", "captured_at_utc", "positions",
                "open_orders", "positions_complete", "orders_complete"}
    if not required <= set(payload):
        raise ValueError("MISSING_BROKER_EVIDENCE_FIELD")
    if payload["source"] not in ("DEGIRO_EXPORT", "DEGIRO_SCREENSHOT", "MANUAL_ENTRY"):
        raise ValueError("INVALID_BROKER_SOURCE")
    if not isinstance(payload["account_scope"], str) or not payload["account_scope"].strip():
        raise ValueError("INVALID_ACCOUNT_SCOPE")
    if not isinstance(payload["captured_at_utc"], str):
        raise ValueError("INVALID_CAPTURE_TIME")
    try:
        captured = datetime.fromisoformat(payload["captured_at_utc"].replace("Z", "+00:00"))
    except ValueError:
        raise ValueError("INVALID_CAPTURE_TIME") from None
    if captured.tzinfo is None or captured.utcoffset() is None:
        raise ValueError("INVALID_CAPTURE_TIME")
    age = (now_utc.astimezone(timezone.utc) - captured.astimezone(timezone.utc)).total_seconds()/3600
    if age < 0:
        raise ValueError("FUTURE_CAPTURE_TIME")
    for field in ("positions_complete", "orders_complete"):
        if not isinstance(payload[field], bool):
            raise ValueError("INVALID_COMPLETENESS_CLAIM")
    if not isinstance(payload["positions"], dict) or not isinstance(payload["open_orders"], list):
        raise ValueError("INVALID_BROKER_COLLECTION")
    for symbol, shares in payload["positions"].items():
        if (not isinstance(symbol, str) or not symbol.strip() or
                not isinstance(shares, (int, float)) or isinstance(shares, bool)
                or not math.isfinite(shares) or shares < 0):
            raise ValueError("INVALID_POSITION")
    for order in payload["open_orders"]:
        if (not isinstance(order, dict) or
                not isinstance(order.get("symbol"), str) or not order["symbol"].strip() or
                order.get("side") not in ("BUY", "SELL") or
                not isinstance(order.get("remaining_quantity"), (int, float)) or
                isinstance(order["remaining_quantity"], bool) or
                not math.isfinite(order["remaining_quantity"]) or order["remaining_quantity"] <= 0):
            raise ValueError("INVALID_OPEN_ORDER")
    return {
        "status": "RESEARCH_ONLY_UNAUTHENTICATED_BROKER_EVIDENCE",
        "source_claim": payload["source"],
        "account_scope_claim": payload["account_scope"],
        "captured_at_utc": captured.isoformat(),
        "age_hours": round(age, 3),
        "fresh": age <= max_age_hours,
        "positions_complete_claim": payload["positions_complete"],
        "orders_complete_claim": payload["orders_complete"],
        "observed_position_symbols": sorted(s for s, q in payload["positions"].items() if q > 0),
        "observed_open_order_count": len(payload["open_orders"]),
        "external_authentication_verified": False,
        "completeness_independently_verified": False,
        "actual_cash_verified": False,
        "capacity_usable": False,
        "trade_ready": False,
        "automatic_orders": False,
    }
