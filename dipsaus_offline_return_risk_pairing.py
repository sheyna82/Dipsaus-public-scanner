"""Pair same-event return and downside outcomes without inventing a score.

A paired report keeps the two metrics visible rather than compressing them
into an optimized risk-adjusted number. Offline descriptive research only.
"""


def pair_return_and_downside(returns, downside):
    if not isinstance(returns, dict) or not isinstance(downside, dict):
        return {"status": "DATA_BLOCKED", "reason": "invalid_inputs", "trade_ready": False}
    if (returns.get("status") != "EXPLORATORY_MATCHED_DATES"
            or downside.get("status") != "EXPLORATORY_MATCHED_DOWNSIDE"):
        return {"status": "DATA_BLOCKED", "reason": "upstream_rejected", "trade_ready": False}
    a, b = returns.get("rows"), downside.get("rows")
    if not isinstance(a, list) or not isinstance(b, list) or len(a) != len(b):
        return {"status": "DATA_BLOCKED", "reason": "event_count_mismatch", "trade_ready": False}
    paired = []
    for r, d in zip(a, b):
        if not isinstance(r, dict) or not isinstance(d, dict) or r.get("signal_date") != d.get("signal_date"):
            return {"status": "DATA_BLOCKED", "reason": "event_date_mismatch", "trade_ready": False}
        try:
            excess = float(r["excess_pct_points"])
            extra_downside = float(d["extra_adverse_pct_points"])
            from math import isfinite
            if not isfinite(excess) or not isfinite(extra_downside) or extra_downside > 0:
                raise ValueError
        except (KeyError, TypeError, ValueError):
            return {"status": "DATA_BLOCKED", "reason": "invalid_metric", "trade_ready": False}
        paired.append({"signal_date": r["signal_date"], "excess_pct_points": excess,
                       "extra_adverse_pct_points": extra_downside,
                       "beat_market": excess > 0,
                       "deeper_than_market": extra_downside < 0})
    return {"status": "EXPLORATORY_RETURN_RISK_PAIRING", "events": len(paired),
            "rows": paired,
            "beat_market_count": sum(x["beat_market"] for x in paired),
            "beat_market_with_deeper_drawdown_count": sum(
                x["beat_market"] and x["deeper_than_market"] for x in paired),
            "independent_holdout": False, "trade_ready": False}
