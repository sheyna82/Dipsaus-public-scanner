"""Offline evidence gate for European financial inputs.

Never trusts a 'verified' flag as external attestation. Checks immutable
record identifiers, price-unit alignment, timestamps and cost assumptions.
No network, broker actions, notifications, or trade authorization.
"""
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from urllib.parse import urlparse

def _decimal(x):
    if isinstance(x, bool) or not isinstance(x, (str, int, Decimal)):
        return None
    try:
        v = Decimal(str(x))
        return v if v.is_finite() and v > 0 else None
    except InvalidOperation:
        return None

def audit_eu_financial_inputs(inputs, *, now_utc, max_quote_age_seconds=900):
    blocks = []
    if not isinstance(inputs, dict) or not isinstance(now_utc, datetime) or now_utc.tzinfo is None:
        return {"status": "BLOCKED", "blocks": ["INVALID_INPUT"], "trade_ready": False, "order_placement_enabled": False}
    if not isinstance(max_quote_age_seconds, (int, float)) or isinstance(max_quote_age_seconds, bool) or not 0 < max_quote_age_seconds <= 86400:
        return {"status": "BLOCKED", "blocks": ["INVALID_MAX_QUOTE_AGE"], "trade_ready": False, "order_placement_enabled": False}
    unit = inputs.get("quote_unit")
    if unit not in ("EUR", "GBp", "GBP", "CHF", "SEK", "NOK", "DKK"):
        blocks.append("QUOTE_UNIT_UNSUPPORTED")
    for role in ("ask", "target_bid", "invalidation", "fx", "fees"):
        record = inputs.get(role + "_evidence")
        if not isinstance(record, dict):
            blocks.append(role.upper() + "_EVIDENCE_MISSING")
            continue
        fields = ("provider_id", "source_record_id", "source_url", "checked_utc")
        if any(not isinstance(record.get(k), str) or not record[k].strip() for k in fields):
            blocks.append(role.upper() + "_PROVENANCE_INCOMPLETE")
            continue
        url = urlparse(record["source_url"])
        if url.scheme != "https" or not url.hostname or url.username or url.password:
            blocks.append(role.upper() + "_URL_INVALID")
        try:
            ts = datetime.fromisoformat(record["checked_utc"].replace("Z", "+00:00"))
            age = (now_utc.astimezone(timezone.utc) - ts.astimezone(timezone.utc)).total_seconds()
            if ts.tzinfo is None or not 0 <= age <= (max_quote_age_seconds if role == "ask" else 86400):
                blocks.append(role.upper() + "_STALE_OR_FUTURE")
        except (TypeError, ValueError, AttributeError):
            blocks.append(role.upper() + "_STALE_OR_FUTURE")
        if role in ("ask", "target_bid", "invalidation"):
            if record.get("quote_unit") != unit:
                blocks.append(role.upper() + "_UNIT_MISMATCH")
            observed = _decimal(record.get("observed_price"))
            claimed = _decimal(inputs.get(role))
            if observed is None or claimed is None or observed != claimed:
                blocks.append(role.upper() + "_PRICE_MISMATCH")
        if role == "fx":
            expected = "EUR" if unit == "EUR" else ("GBP" if unit == "GBp" else unit)
            if record.get("source_currency") != expected or record.get("target_currency") != "EUR":
                blocks.append("FX_PAIR_MISMATCH")
            if unit != "EUR" and _decimal(record.get("eur_per_base_unit")) != _decimal(inputs.get("eur_per_base_unit")):
                blocks.append("FX_RATE_MISMATCH")
        if role == "fees":
            for field in ("buy_fee_eur", "sell_fee_eur", "buy_fx_rate", "sell_fx_rate"):
                # Zero fees are valid; explicit nonnegative numeric evidence required.
                try:
                    observed = Decimal(str(record[field]))
                    expected = Decimal(str(inputs[field]))
                    if isinstance(record[field], bool) or isinstance(inputs[field], bool) or not observed.is_finite() or observed < 0 or observed != expected:
                        raise ValueError
                except (KeyError, InvalidOperation, ValueError, TypeError):
                    blocks.append("FEES_MISMATCH")
                    break
    # Even perfectly formatted evidence is not a trusted independent capture.
    blocks.append("EXTERNAL_SOURCE_ATTESTATION_NOT_CONNECTED")
    return {"status": "BLOCKED", "blocks": list(dict.fromkeys(blocks)),
            "trade_ready": False, "order_placement_enabled": False}
