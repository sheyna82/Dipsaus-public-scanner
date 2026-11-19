"""Fail-closed DEGIRO evidence consistency checks; no broker authentication.

All fields are untrusted assertions until independently verified. This module
cannot enable orders, attest a broker connection or validate actual execution.
"""
from datetime import datetime, timezone

BLOCKED = {"trade_ready": False, "order_placement_enabled": False,
           "broker_route_verified": False, "degiro_fee_verified": False,
           "source_authenticity_independently_verified": False}
REQUIRED = ("isin", "operating_mic", "quote_source", "fee_source",
            "route_source", "quote_observed_utc", "quote_bid", "quote_ask",
            "fee_buy_eur", "fee_sell_eur", "route_instrument_isin",
            "route_operating_mic")

def inspect_degiro_evidence(evidence, *, now):
    base = {**BLOCKED, "status": "DEGIRO_EVIDENCE_BLOCKED"}
    if not isinstance(evidence, dict) or not isinstance(now, datetime) or now.utcoffset() is None:
        return {**base, "reason": "INVALID_INPUT"}
    missing = [key for key in REQUIRED if key not in evidence]
    if missing:
        return {**base, "reason": "MISSING_FIELDS", "missing": missing}
    if (evidence["quote_source"] != "DEGIRO" or evidence["fee_source"] != "DEGIRO"
            or evidence["route_source"] != "DEGIRO"):
        return {**base, "reason": "NON_BROKER_SOURCE"}
    if (evidence["route_instrument_isin"] != evidence["isin"]
            or evidence["route_operating_mic"] != evidence["operating_mic"]):
        return {**base, "reason": "ROUTE_IDENTITY_MISMATCH"}
    if (not isinstance(evidence["isin"], str) or not isinstance(evidence["operating_mic"], str)
            or len(evidence["operating_mic"]) != 4):
        return {**base, "reason": "INVALID_IDENTITY"}
    try:
        timestamp = datetime.fromisoformat(evidence["quote_observed_utc"].replace("Z", "+00:00"))
        age = (now.astimezone(timezone.utc) - timestamp.astimezone(timezone.utc)).total_seconds()
    except (AttributeError, ValueError, TypeError):
        return {**base, "reason": "INVALID_QUOTE_TIMESTAMP"}
    if not 0 <= age <= 120:
        return {**base, "reason": "STALE_OR_FUTURE_QUOTE"}
    values = [evidence[key] for key in ("quote_bid", "quote_ask", "fee_buy_eur", "fee_sell_eur")]
    import math
    if any(type(value) not in (int, float) or not math.isfinite(value) for value in values):
        return {**base, "reason": "INVALID_NUMERIC_EVIDENCE"}
    bid, ask, buy_fee, sell_fee = values
    if bid <= 0 or ask < bid or min(buy_fee, sell_fee) < 0:
        return {**base, "reason": "INVALID_MARKET_VALUES"}
    return {**BLOCKED, "status": "DEGIRO_CLAIMS_STRUCTURALLY_CONSISTENT",
            "quote_age_seconds": age,
            "note": "Source labels and values are untrusted; independent broker authentication is absent."}
