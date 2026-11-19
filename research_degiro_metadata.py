"""Offline freshness checks for DEGIRO fee and route claims.

Metadata is untrusted. Passing freshness checks cannot authenticate a broker.
"""
from datetime import datetime, timezone

BLOCKED = {"trade_ready": False, "order_placement_enabled": False,
           "broker_route_verified": False, "degiro_fee_verified": False,
           "source_authenticity_independently_verified": False}

def inspect_broker_metadata_freshness(evidence, *, now):
    base = {**BLOCKED, "status": "BROKER_METADATA_BLOCKED"}
    if not isinstance(evidence, dict) or not isinstance(now, datetime) or now.utcoffset() is None:
        return {**base, "reason": "INVALID_INPUT"}
    for group, key, max_age in (("fees", "fee_observed_utc", 30 * 86400),
                                 ("route", "route_observed_utc", 86400)):
        raw = evidence.get(key)
        if not isinstance(raw, str):
            return {**base, "reason": "MISSING_METADATA_TIMESTAMP", "group": group}
        try:
            stamp = datetime.fromisoformat(raw.replace("Z", "+00:00"))
            if stamp.utcoffset() is None:
                raise ValueError("naive")
            age = (now.astimezone(timezone.utc) - stamp.astimezone(timezone.utc)).total_seconds()
        except (ValueError, OverflowError):
            return {**base, "reason": "INVALID_METADATA_TIMESTAMP", "group": group}
        if not 0 <= age <= max_age:
            return {**base, "reason": "STALE_OR_FUTURE_METADATA", "group": group}
    return {**BLOCKED, "status": "BROKER_METADATA_CLAIMS_FRESH",
            "note": "Timestamps are untrusted assertions; independent authentication absent."}
