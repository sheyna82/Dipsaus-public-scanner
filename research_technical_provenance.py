"""Research-only structural checks for technical-level provenance.

All metadata is untrusted; passing checks never attests an analyst or source.
"""
from datetime import datetime, timezone

BLOCKED = {"trade_ready": False, "order_placement_enabled": False,
           "technical_levels_independently_verified": False,
           "source_authenticity_independently_verified": False}

def inspect_technical_level_claims(technical, broker, *, now):
    base = {**BLOCKED, "status": "TECHNICAL_PROVENANCE_BLOCKED"}
    if (not isinstance(technical, dict) or not isinstance(broker, dict)
            or not isinstance(now, datetime) or now.utcoffset() is None):
        return {**base, "reason": "INVALID_INPUT"}
    if (technical.get("instrument_isin") != broker.get("isin")
            or technical.get("operating_mic") != broker.get("operating_mic")
            or not isinstance(technical.get("instrument_isin"), str)
            or not isinstance(technical.get("operating_mic"), str)):
        return {**base, "reason": "TECHNICAL_INSTRUMENT_MISMATCH"}
    raw = technical.get("levels_observed_utc")
    if not isinstance(raw, str):
        return {**base, "reason": "MISSING_LEVEL_TIMESTAMP"}
    try:
        stamp = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        if stamp.utcoffset() is None:
            raise ValueError("timezone required")
        age = (now.astimezone(timezone.utc) - stamp.astimezone(timezone.utc)).total_seconds()
    except (ValueError, OverflowError):
        return {**base, "reason": "INVALID_LEVEL_TIMESTAMP"}
    if not 0 <= age <= 86400:
        return {**base, "reason": "STALE_OR_FUTURE_LEVELS"}
    return {**BLOCKED, "status": "TECHNICAL_CLAIMS_STRUCTURALLY_CONSISTENT",
            "note": "Technical timestamps and instrument identifiers are untrusted assertions."}
