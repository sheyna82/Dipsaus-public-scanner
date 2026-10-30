"""Offline baseline comparison for historical event research.

Inputs must already be validated and aligned to the same session dates.
This computes observed excess returns; it does not establish predictive skill.
"""
from decimal import Decimal, InvalidOperation


def compare_event_to_benchmark(stock_closes, benchmark_closes, *, horizons=(1, 3, 5)):
    if not isinstance(stock_closes, list) or not isinstance(benchmark_closes, list):
        raise ValueError("series_must_be_lists")
    if len(stock_closes) != len(benchmark_closes) or len(stock_closes) < max(horizons) + 1:
        raise ValueError("insufficient_aligned_sessions")

    def normalized(series):
        values = []
        previous = None
        for entry in series:
            if not isinstance(entry, dict) or set(entry) != {"date", "close"}:
                raise ValueError("invalid_session_record")
            day = entry["date"]
            if not isinstance(day, str) or (previous is not None and day <= previous):
                raise ValueError("unsorted_session_dates")
            from datetime import date
            try:
                date.fromisoformat(day)
                price = Decimal(str(entry["close"]))
            except (ValueError, InvalidOperation, TypeError) as exc:
                raise ValueError("invalid_session_price") from exc
            if not price.is_finite() or price <= 0:
                raise ValueError("invalid_session_price")
            values.append((day, price))
            previous = day
        return values

    stocks, benchmark = normalized(stock_closes), normalized(benchmark_closes)
    if [x[0] for x in stocks] != [x[0] for x in benchmark]:
        raise ValueError("stock_benchmark_dates_mismatch")
    if any(not isinstance(h, int) or isinstance(h, bool) or h < 1 for h in horizons):
        raise ValueError("invalid_horizons")
    results = []
    for horizon in horizons:
        if horizon >= len(stocks):
            raise ValueError("insufficient_aligned_sessions")
        stock_return = stocks[horizon][1] / stocks[0][1] - 1
        baseline_return = benchmark[horizon][1] / benchmark[0][1] - 1
        results.append({
            "sessions_after_baseline": horizon,
            "ending_session": stocks[horizon][0],
            "stock_return_pct": str(stock_return * 100),
            "benchmark_return_pct": str(baseline_return * 100),
            "excess_return_percentage_points": str((stock_return - baseline_return) * 100),
        })
    return {
        "baseline_session": stocks[0][0],
        "horizons": results,
        "calendar_independently_verified": False,
        "vendor_prices_independently_verified": False,
        "event_time_verified": False,
        "predictive_skill_established": False,
        "trade_ready": False,
    }
