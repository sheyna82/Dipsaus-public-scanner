"""Research-only benchmark market trend join, with no forward fill.

The market trend uses the benchmark's current close versus its close 20
benchmark trading sessions earlier. Missing dates remain missing.
"""
import csv
import io
from research_daily_price_csv_audit import audit_daily_price_csv


def attach_market_trend(events, benchmark_payload, *, lookback=20):
    audit_daily_price_csv(benchmark_payload)
    if type(lookback) is not int or lookback < 1:
        raise ValueError("invalid_lookback")
    if not isinstance(events, list):
        raise ValueError("invalid_events")
    bars = list(csv.DictReader(io.StringIO(benchmark_payload.decode("utf-8-sig"))))
    trends = {}
    for i in range(lookback, len(bars)):
        trends[bars[i]["date"]] = (
            float(bars[i]["close"]) > float(bars[i - lookback]["close"]))
    result = []
    for event in events:
        if not isinstance(event, dict) or not isinstance(event.get("date"), str):
            raise ValueError("invalid_event")
        flag = trends.get(event["date"])
        result.append({**event, "market_20d_positive": flag,
                       "point_in_time_verified": False, "trade_ready": False})
    return result


def eligible_model_rows(events):
    """Explicitly exclude missing benchmark dates; never infer their trend."""
    if not isinstance(events, list):
        raise ValueError("invalid_events")
    return [row for row in events if type(row.get("market_20d_positive")) is bool]
