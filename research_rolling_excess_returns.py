"""Offline, no-lookahead rolling relative-return evaluation for research evidence only."""
from decimal import Decimal, InvalidOperation


def rolling_excess_returns(stock_rows, benchmark_rows, *, horizons=(1, 3, 5)):
    if not isinstance(stock_rows, list) or not isinstance(benchmark_rows, list):
        raise ValueError("invalid_series")
    if not isinstance(horizons, tuple) or not horizons or any(type(h) is not int or h < 1 for h in horizons):
        raise ValueError("invalid_horizons")
    def clean(rows):
        out = {}
        last = ""
        for row in rows:
            if not isinstance(row, dict) or set(row) != {"date", "close"}:
                raise ValueError("invalid_row")
            day = row["date"]
            if not isinstance(day, str) or len(day) != 10 or day <= last:
                raise ValueError("invalid_order")
            from datetime import date
            try:
                date.fromisoformat(day)
                close = Decimal(str(row["close"]))
            except (ValueError, TypeError, InvalidOperation) as exc:
                raise ValueError("invalid_price") from exc
            if not close.is_finite() or close <= 0:
                raise ValueError("invalid_price")
            out[day] = close
            last = day
        return out
    stocks, spy = clean(stock_rows), clean(benchmark_rows)
    dates = sorted(stocks.keys() & spy.keys())
    if len(dates) <= max(horizons):
        raise ValueError("insufficient_shared_sessions")
    observations = []
    for index, start in enumerate(dates):
        for horizon in horizons:
            if index + horizon >= len(dates):
                continue
            end = dates[index + horizon]
            stock_ret = (stocks[end] / stocks[start] - 1) * 100
            spy_ret = (spy[end] / spy[start] - 1) * 100
            observations.append({
                "start_session": start, "end_session": end, "horizon": horizon,
                "stock_return_pct": str(stock_ret),
                "benchmark_return_pct": str(spy_ret),
                "excess_percentage_points": str(stock_ret - spy_ret)})
    return {"observations": observations, "uses_future_prices_for_features": False,
            "predictive_skill_established": False, "trade_ready": False}
