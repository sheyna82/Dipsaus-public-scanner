"""Explain missing event quote metadata without making a trading decision.

Pure offline diagnostics for existing Yahoo watch report rows.
"""
from event_provider_quote_adapter import provider_event_quote_metrics

REQUIRED_FIELDS = (
    "symbol", "provider_symbol", "provider_currency", "provider_quote",
    "provider_quote_utc", "provider_freshness_pass", "provider_source",
    "market_session_verified", "provider_delayed",
)

def diagnose_event_quote_row(row, expected_symbol, now, expected_currency="USD"):
    """Return an auditable research-only diagnosis; never infer missing evidence."""
    if not isinstance(row, dict):
        return {"status": "BLOCKED", "missing_fields": list(REQUIRED_FIELDS),
                "invalid_fields": [], "fresh_quote": None, "execution_ready": False}
    missing = [key for key in REQUIRED_FIELDS if key not in row or row[key] is None]
    invalid = []
    for key in ("symbol", "provider_symbol"):
        if key not in missing and row[key] != expected_symbol:
            invalid.append(key)
    if "provider_currency" not in missing and (expected_currency is not None and row["provider_currency"] != expected_currency):
        invalid.append("provider_currency")
    for key, required in (("provider_freshness_pass", True),
                          ("market_session_verified", True),
                          ("provider_delayed", False)):
        if key not in missing and row[key] is not required:
            invalid.append(key)
    metrics = provider_event_quote_metrics(row, expected_symbol, now, expected_currency)
    evidence = metrics.get("fresh_quote")
    return {"status": "VALIDATED_RESEARCH_QUOTE" if evidence else "BLOCKED",
            "missing_fields": missing, "invalid_fields": invalid,
            "fresh_quote": evidence, "execution_ready": False}
