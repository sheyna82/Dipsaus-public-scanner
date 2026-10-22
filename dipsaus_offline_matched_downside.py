"""Matched-window intraperiod downside comparison, offline research only.

Measures adverse excursion from next-session open to the lowest subsequent
daily low through exit, not an executable stop-loss or a portfolio drawdown.
"""


def matched_downside(stock, benchmark, signal_indices, *, horizon=10):
    if (type(horizon) is not int or horizon < 1 or
            not isinstance(stock, (list, tuple)) or
            not isinstance(benchmark, (list, tuple)) or
            not isinstance(signal_indices, (list, tuple)) or
            not stock or len(stock) != len(benchmark) or
            not all(isinstance(x, dict) for x in [*stock, *benchmark])):
        return {"status": "DATA_BLOCKED", "reason": "invalid_input", "trade_ready": False}
    dates = [r.get("date") for r in stock]
    if dates != [r.get("date") for r in benchmark] or any(not isinstance(d, str) or not d for d in dates) or len(dates) != len(set(dates)) or dates != sorted(dates):
        return {"status": "DATA_BLOCKED", "reason": "unaligned_sessions", "trade_ready": False}
    from math import isfinite
    results = []
    previous_exit = -1
    for i in signal_indices:
        if type(i) is not int or i < 0 or i <= previous_exit or i + horizon + 1 >= len(stock):
            return {"status": "DATA_BLOCKED", "reason": "overlap_or_invalid_index", "trade_ready": False}
        entry, end = i + 1, i + horizon + 1
        values = []
        for bars in (stock, benchmark):
            try:
                opening = float(bars[entry]["open"])
                lows = [float(r["low"]) for r in bars[entry:end + 1]]
                if not isfinite(opening) or opening <= 0 or not all(isfinite(x) and x > 0 for x in lows):
                    raise ValueError
            except (KeyError, TypeError, ValueError):
                return {"status": "DATA_BLOCKED", "reason": "invalid_price", "trade_ready": False}
            values.append(round(100 * (min(lows) / opening - 1), 6))
        results.append({"signal_date": dates[i], "stock_adverse_pct": min(0.0, values[0]),
                        "benchmark_adverse_pct": min(0.0, values[1]),
                        "extra_adverse_pct_points": round(min(0.0, values[0]) - min(0.0, values[1]), 6)})
        previous_exit = end
    return {"status": "EXPLORATORY_MATCHED_DOWNSIDE", "events": len(results),
            "rows": results,
            "mean_extra_adverse_pct_points": round(sum(r["extra_adverse_pct_points"] for r in results) / len(results), 6) if results else None,
            "independent_holdout": False, "trade_ready": False}
