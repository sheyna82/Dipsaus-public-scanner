"""Research-only transparent downside-risk aggregate for chronological holdouts.

Reports pooled *event* counts, not independent observations or portfolio P&L.
No thresholds are tuned and no live scanner integration is performed.
"""


def summarize_holdouts(symbol_results):
    records = []
    for item in symbol_results:
        holdout = item.get("chronological_holdout", {})
        test = holdout.get("test", {})
        if (holdout.get("status") != "DESCRIPTIVE_CHRONOLOGICAL_SPLIT"
                or not isinstance(test.get("count"), int)
                or test["count"] < 0
                or (test["count"] and not isinstance(test.get("mean_net_pct"), (int, float)))):
            return {"status": "DATA_BLOCKED", "reason": "missing_holdout",
                    "predictive_edge_proven": False, "trade_ready": False}
        records.append((item.get("symbol"), test))
    n = sum(t["count"] for _, t in records)
    adverse = sum(t["severe_intraperiod_drawdown_count"] for _, t in records)
    positive = sum(t["positive_count"] for _, t in records)
    if any(t["severe_intraperiod_drawdown_count"] > t["count"]
           or t["positive_count"] > t["count"] for _, t in records):
        return {"status": "DATA_BLOCKED", "reason": "inconsistent_counts",
                "predictive_edge_proven": False, "trade_ready": False}
    return {"status": "DESCRIPTIVE_RISK_AGGREGATE",
            "symbol_count": len(records), "event_count": n,
            "positive_event_count": positive,
            "severe_intraperiod_drawdown_event_count": adverse,
            "severe_intraperiod_drawdown_event_rate_pct": round(100 * adverse / n, 2) if n else None,
            "event_weighted_mean_net_pct": round(
                sum(t["count"] * t["mean_net_pct"] for _, t in records) / n, 5) if n else None,
            "independent_events_assumed": False,
            "adjustments_independently_verified": False,
            "earnings_dates_verified": False,
            "predictive_edge_proven": False, "trade_ready": False}
