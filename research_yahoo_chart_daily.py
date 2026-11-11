"""Strict offline Yahoo Finance chart normalization (unverified vendor evidence)."""
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation


def parse_yahoo_chart_daily(payload, *, expected_symbol):
    if not isinstance(payload, dict) or not isinstance(expected_symbol, str) or not expected_symbol:
        raise ValueError("invalid_chart_request")
    chart = payload.get("chart")
    if not isinstance(chart, dict) or chart.get("error") is not None:
        raise ValueError("vendor_chart_error")
    results = chart.get("result")
    if not isinstance(results, list) or len(results) != 1:
        raise ValueError("invalid_chart_results")
    item = results[0]
    if not isinstance(item, dict) or not isinstance(item.get("meta"), dict):
        raise ValueError("missing_chart_metadata")
    if item["meta"].get("symbol", "").upper() != expected_symbol.upper():
        raise ValueError("unexpected_symbol")
    timestamps = item.get("timestamp")
    indicators = item.get("indicators")
    if not isinstance(indicators, dict):
        raise ValueError("missing_indicators")
    quote = indicators.get("quote")
    if not isinstance(quote, list) or len(quote) != 1 or not isinstance(quote[0], dict):
        raise ValueError("missing_quote")
    closes = quote[0].get("close")
    if not isinstance(timestamps, list) or not isinstance(closes, list) or len(timestamps) != len(closes) or not timestamps:
        raise ValueError("unaligned_chart_series")
    from zoneinfo import ZoneInfo
    market_tz = ZoneInfo("America/New_York")
    output = []
    previous = None
    for stamp, close in zip(timestamps, closes):
        if type(stamp) is not int or stamp < 0:
            raise ValueError("invalid_chart_timestamp")
        day = datetime.fromtimestamp(stamp, timezone.utc).astimezone(market_tz).date().isoformat()
        if previous is not None and day <= previous:
            raise ValueError("nonmonotonic_market_sessions")
        previous = day
        if close is None:
            continue  # vendor may include an incomplete session; do not synthesize a price
        try:
            value = Decimal(str(close))
        except (ValueError, InvalidOperation, TypeError) as exc:
            raise ValueError("invalid_chart_price") from exc
        if not value.is_finite() or value <= 0:
            raise ValueError("invalid_chart_price")
        output.append({"date": day, "close": str(value)})
    if not output:
        raise ValueError("no_complete_chart_prices")
    return output
