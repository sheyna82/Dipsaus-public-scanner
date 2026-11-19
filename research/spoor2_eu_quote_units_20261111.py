"""Spoor 2: isolated European quotation-unit normalization.

No market feed, FX lookup, broker API, or trade authorization. Decimal values
are exact; conversion to EUR requires separately sourced, reviewed FX evidence.
"""
from decimal import Decimal, InvalidOperation
from datetime import datetime, timezone

CURRENCY_UNITS = {"EUR": ("EUR", Decimal("1")),
                  "USD": ("USD", Decimal("1")),
                  "GBP": ("GBP", Decimal("1")),
                  "GBp": ("GBP", Decimal("0.01")),
                  "CHF": ("CHF", Decimal("1")),
                  "SEK": ("SEK", Decimal("1")),
                  "NOK": ("NOK", Decimal("1")),
                  "DKK": ("DKK", Decimal("1"))}

def normalize_quote(value, unit):
    result = {"status": "BLOCKED", "trade_ready": False,
              "order_placement_enabled": False}
    if unit not in CURRENCY_UNITS:
        return {**result, "blocks": ["UNSUPPORTED_QUOTE_UNIT"]}
    if isinstance(value, bool) or not isinstance(value, (str, int, Decimal)):
        return {**result, "blocks": ["INVALID_QUOTE_VALUE"]}
    try:
        price = Decimal(str(value))
    except InvalidOperation:
        return {**result, "blocks": ["INVALID_QUOTE_VALUE"]}
    if not price.is_finite() or price <= 0:
        return {**result, "blocks": ["INVALID_QUOTE_VALUE"]}
    currency, factor = CURRENCY_UNITS[unit]
    normalized = price * factor
    return {**result, "status": "NORMALIZED_RESEARCH_ONLY", "blocks": [],
            "source_unit": unit, "base_currency": currency,
            "base_price": str(normalized), "fx_verified": False}

def review_fx_evidence(fx, *, now_utc, max_age_seconds=900):
    result = {"status": "BLOCKED", "blocks": [], "trade_ready": False,
              "order_placement_enabled": False}
    if not isinstance(fx, dict) or not isinstance(now_utc, datetime) or now_utc.tzinfo is None:
        return {**result, "blocks": ["INVALID_FX_EVIDENCE"]}
    if not isinstance(max_age_seconds, (int, float)) or isinstance(max_age_seconds, bool) or not 0 < max_age_seconds <= 86400:
        return {**result, "blocks": ["INVALID_FX_MAX_AGE"]}
    if fx.get("source_currency") not in ("GBP", "CHF", "SEK", "NOK", "DKK", "USD") or fx.get("target_currency") != "EUR":
        return {**result, "blocks": ["FX_PAIR_UNSUPPORTED"]}
    if fx.get("verified") is not True:
        result["blocks"].append("FX_NOT_INDEPENDENTLY_VERIFIED")
    for key in ("provider_id", "source_record_id", "source_url"):
        if not isinstance(fx.get(key), str) or not fx[key].strip():
            result["blocks"].append("FX_PROVENANCE_MISSING")
            break
    try:
        rate = Decimal(str(fx["eur_per_base_unit"]))
        if isinstance(fx["eur_per_base_unit"], bool) or not rate.is_finite() or rate <= 0:
            raise InvalidOperation
    except (KeyError, InvalidOperation, TypeError):
        result["blocks"].append("FX_RATE_INVALID")
    try:
        ts = datetime.fromisoformat(fx["checked_utc"].replace("Z", "+00:00"))
        age = (now_utc.astimezone(timezone.utc) - ts.astimezone(timezone.utc)).total_seconds()
        if ts.tzinfo is None or not 0 <= age <= max_age_seconds:
            result["blocks"].append("FX_STALE_OR_FUTURE")
    except (KeyError, TypeError, ValueError, AttributeError):
        result["blocks"].append("FX_STALE_OR_FUTURE")
    # A declared verified flag is not an independent external attestation.
    result["blocks"].append("FX_EXTERNAL_ATTESTATION_NOT_CONNECTED")
    return result
