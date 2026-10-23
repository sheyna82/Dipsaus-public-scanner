"""Chronological diagnostic split of observed frozen-rule SPY comparisons.

No optimization or model fitting. Test starts after a ten-session embargo;
all matched event windows remain entirely inside their own segment.
Not an untouched external holdout: this research has already been inspected.
"""
from dipsaus_offline_frozen_event_market_bridge import evaluate_frozen_events_against_market


def chronological_matched_risk(stock, benchmark, *, train_fraction=0.7,
                               horizon=10, embargo=10):
    if (type(train_fraction) not in (float, int) or not 0.5 <= train_fraction <= 0.85
            or type(horizon) is not int or horizon < 2
            or type(embargo) is not int or embargo < horizon
            or not isinstance(stock, (list, tuple)) or len(stock) < 70
            or not isinstance(benchmark, (list, tuple)) or len(stock) != len(benchmark)):
        return {"status": "DATA_BLOCKED", "reason": "invalid_split_inputs", "trade_ready": False}
    if [r.get("date") for r in stock if isinstance(r, dict)] != [r.get("date") for r in benchmark if isinstance(r, dict)]:
        return {"status": "DATA_BLOCKED", "reason": "unaligned_dates", "trade_ready": False}
    split = int(len(stock) * train_fraction)
    train = evaluate_frozen_events_against_market(stock[:split], benchmark[:split],
                                                   event_horizon=horizon)
    # Preserve the 21-day feature lookback while excluding embargo-period
    # signals. Signals from this window are deliberately discarded.
    test_start = max(0, split + embargo - 21)
    test = evaluate_frozen_events_against_market(stock[test_start:], benchmark[test_start:],
                                                  event_horizon=horizon)
    if train.get("status") != "EXPLORATORY_COMBINED_RETURN_RISK" or test.get("status") != "EXPLORATORY_COMBINED_RETURN_RISK":
        return {"status": "DATA_BLOCKED", "reason": "segment_evaluation_failed",
                "train_status": train.get("status"), "test_status": test.get("status"),
                "trade_ready": False}
    test_rows = [r for r in test["rows"] if r["signal_date"] >= stock[split + embargo]["date"]]
    def summary(rows):
        n = len(rows)
        return {"events": n,
                "mean_excess_pct_points": round(sum(r["excess_pct_points"] for r in rows) / n, 6) if n else None,
                "mean_extra_adverse_pct_points": round(sum(r["extra_adverse_pct_points"] for r in rows) / n, 6) if n else None,
                "beat_market_count": sum(r["beat_market"] for r in rows),
                "beat_market_with_deeper_drawdown_count": sum(r["beat_market"] and r["deeper_than_market"] for r in rows)}
    return {"status": "EXPLORATORY_CHRONOLOGICAL_DIAGNOSTIC",
            "train_end_date": stock[split - 1]["date"],
            "test_start_date": stock[split + embargo]["date"],
            "embargo_sessions": embargo,
            "train": summary(train["rows"]), "test": summary(test_rows),
            "test_events_sufficient": len(test_rows) >= 30,
            "minimum_test_events": 30,
            "independent_untouched_holdout": False, "survivorship_free": False,
            "earnings_asof_verified": False, "corporate_actions_verified": False,
            "predictive_edge_proven": False, "trade_ready": False}
