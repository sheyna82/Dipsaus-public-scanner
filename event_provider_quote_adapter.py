"""Offline adapter for existing provider quote observations; never fetches data."""
from datetime import datetime
from event_quote_evidence import event_quote_metrics

def provider_event_quote_metrics(row, expected_symbol, now, expected_currency="USD"):
    """Fail closed unless identity, currency, provenance and freshness are explicit.

    The caller must independently establish regular-session suitability.
    Provider observations are not broker executable prices.
    """
    if not isinstance(row, dict) or not isinstance(expected_symbol, str):
        return {}
    symbol = row.get("provider_symbol") or row.get("symbol")
    if not symbol or symbol != expected_symbol:
        return {}
    currency = row.get("provider_currency") or row.get("currency")
    if currency not in ("USD", "EUR", "GBP", "CHF") or currency != expected_currency:
        return {}
    if row.get("provider_freshness_pass") is not True:
        return {}
    if row.get("market_session_verified") is not True:
        return {}
    if row.get("provider_delayed") is not False:
        return {}
    source = row.get("provider_source")
    if not isinstance(source, str) or not source.strip():
        return {}
    if not isinstance(now, datetime):
        return {}
    return event_quote_metrics(row.get("provider_quote"),
                               row.get("provider_quote_utc"), source, now)
