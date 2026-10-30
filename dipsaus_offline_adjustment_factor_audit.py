"""Research-only consistency audit for raw OHLC and adjusted close.

An adjusted close alone cannot establish an adjusted OHLC series without
a documented adjustment policy. We deliberately do not modify prices.
"""


def audit_adjusted_close_factors(rows, *, close_key="close", adjusted_key="adjusted"):
    if not isinstance(rows, list) or len(rows) < 2:
        return {"status": "REJECTED", "reason": "insufficient_rows"}
    factors = []
    for row in rows:
        try:
            close = float(row[close_key])
            adjusted = float(row[adjusted_key])
        except (KeyError, TypeError, ValueError, OverflowError):
            return {"status": "REJECTED", "reason": "invalid_prices"}
        if not (0 < close < float("inf") and 0 < adjusted < float("inf")):
            return {"status": "REJECTED", "reason": "invalid_prices"}
        factors.append(adjusted / close)
    jumps = [i for i in range(1, len(factors))
             if abs(factors[i] / factors[i - 1] - 1) > 0.001]
    return {"status": "RESEARCH_ONLY",
            "rows": len(rows),
            "factor_min": min(factors),
            "factor_max": max(factors),
            "factor_change_events_gt_0_1pct": len(jumps),
            "factor_change_indices": jumps,
            "adjusted_ohlc_constructed": False,
            "policy_verified": False,
            "trade_ready": False}
