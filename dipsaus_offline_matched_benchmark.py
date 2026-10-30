"""Matched-date benchmark comparison for exploratory offline price-only outcomes.

Compares a stock and benchmark bought at the same next-session open and
sold at the same tenth subsequent close. This is not a portfolio simulation
or a valid independent holdout.
"""


def matched_event_comparison(stock, benchmark, signal_indices, *, horizon=10,
                             fee_bps_each_side=10):
    if (type(horizon) is not int or horizon < 1 or
            type(fee_bps_each_side) not in (int, float) or
            not 0 <= fee_bps_each_side <= 200 or
            not isinstance(stock, (list, tuple)) or
            not isinstance(benchmark, (list, tuple)) or
            not isinstance(signal_indices, (list, tuple)) or
            len(stock) != len(benchmark) or not stock):
        return {"status": "DATA_BLOCKED", "reason": "invalid_inputs", "trade_ready": False}
    if [x.get("date") for x in stock if isinstance(x, dict)] != [x.get("date") for x in benchmark if isinstance(x, dict)] or not all(isinstance(x, dict) for x in [*stock, *benchmark]):
        return {"status": "DATA_BLOCKED", "reason": "unaligned_dates", "trade_ready": False}
    rows = []
    previous_exit = -1
    for i in signal_indices:
        if type(i) is not int or i < 0 or i + horizon + 1 >= len(stock) or i <= previous_exit:
            return {"status": "DATA_BLOCKED", "reason": "overlap_or_invalid_index", "trade_ready": False}
        entry_idx, exit_idx = i + 1, i + horizon + 1
        try:
            a, z = float(stock[entry_idx]["open"]), float(stock[exit_idx]["close"])
            ba, bz = float(benchmark[entry_idx]["open"]), float(benchmark[exit_idx]["close"])
            from math import isfinite
            if not all(isfinite(v) and v > 0 for v in (a, z, ba, bz)):
                raise ValueError("nonpositive price")
        except (KeyError, TypeError, ValueError):
            return {"status": "DATA_BLOCKED", "reason": "invalid_price", "trade_ready": False}
        cost = 2 * fee_bps_each_side / 100
        stock_net = 100 * (z / a - 1) - cost
        bench_net = 100 * (bz / ba - 1) - cost
        rows.append({"signal_date": stock[i]["date"], "exit_date": stock[exit_idx]["date"],
                     "stock_net_pct": round(stock_net, 6),
                     "benchmark_net_pct": round(bench_net, 6),
                     "excess_pct_points": round(stock_net - bench_net, 6)})
        previous_exit = exit_idx
    return {"status": "EXPLORATORY_MATCHED_DATES", "events": len(rows),
            "rows": rows,
            "mean_excess_pct_points": round(sum(r["excess_pct_points"] for r in rows) / len(rows), 6) if rows else None,
            "adjustments_independently_verified": False,
            "independent_holdout": False, "trade_ready": False}
