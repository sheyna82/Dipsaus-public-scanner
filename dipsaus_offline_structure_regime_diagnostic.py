"""Predeclared descriptive regime/structure annotations for frozen recovery events.

No optimized thresholds, no new signals, no live trading integration.
"""
from statistics import median
from dipsaus_offline_frozen_rs_atr import annotate_frozen_events_rs_atr


def evaluate_structure_regime(stock, benchmark, *, horizon=10, train_fraction=0.7,
                              embargo_sessions=10, min_train=15, min_test=10):
    result = annotate_frozen_events_rs_atr(stock, benchmark, horizon=horizon)
    if result.get("status") != "EXPLORATORY_FROZEN_RS_ATR":
        return {"status": "DATA_BLOCKED", "reason": result.get("reason", "source_quality"), "trade_ready": False}
    if (not 0.5 <= train_fraction <= 0.85 or type(embargo_sessions) is not int
            or embargo_sessions < horizon):
        return {"status": "DATA_BLOCKED", "reason": "invalid_split", "trade_ready": False}
    split = int(len(stock) * train_fraction)
    dates = {bar["date"]: i for i, bar in enumerate(stock)}
    train, test = [], []
    for row in result["rows"]:
        i = dates[row["signal_date"]]
        if i < 21:
            return {"status": "DATA_BLOCKED", "reason": "feature_history", "trade_ready": False}
        closes = [b["close"] for b in stock]
        benchmark_closes = [b["close"] for b in benchmark]
        features = {
            "structure_above_20d_mean": closes[i] > sum(closes[i-19:i+1]) / 20,
            "atr_expanding": row["atr_14d_pct"] > 100 * (
                sum(max(stock[j]["high"]-stock[j]["low"],
                        abs(stock[j]["high"]-stock[j-1]["close"]),
                        abs(stock[j]["low"]-stock[j-1]["close"])) for j in range(i-18, i-4)) / 14
                ) / closes[i-5] if i >= 19 else False,
            "market_20d_positive": benchmark_closes[i] > benchmark_closes[i-20],
        }
        record = {**row, **features}
        if i + horizon < split:
            train.append(record)
        elif i >= split + embargo_sessions:
            test.append(record)
    if len(train) < min_train or len(test) < min_test:
        return {"status": "DATA_BLOCKED", "reason": "insufficient_split_events",
                "train_events": len(train), "test_events": len(test), "trade_ready": False}

    def metrics(rows):
        if not rows:
            return None
        return {"events": len(rows),
                "mean_net_return_pct": round(sum(r["terminal_return_net_pct"] for r in rows)/len(rows), 5),
                "mean_adverse_excursion_pct": round(sum(r["max_adverse_excursion_pct"] for r in rows)/len(rows), 5),
                "severe_adverse_rate_pct": round(100*sum(r["max_adverse_excursion_pct"] <= -3 for r in rows)/len(rows), 3),
                "winning_events": sum(r["terminal_return_net_pct"] > 0 for r in rows)}
    factors = {}
    for key in ("structure_above_20d_mean", "atr_expanding", "market_20d_positive"):
        selected = [r for r in test if r[key]]
        skipped = [r for r in test if not r[key]]
        factors[key] = {"selected": metrics(selected), "skipped": metrics(skipped),
                        "missed_winning_events": sum(r["terminal_return_net_pct"] > 0 for r in skipped)}
    return {"status": "EXPLORATORY_STRUCTURE_REGIME_DIAGNOSTIC",
            "train_events": len(train), "test_events": len(test),
            "baseline_test": metrics(test), "factors": factors,
            "independent_untouched_holdout": False, "source_verified": False,
            "predictive_edge_proven": False, "trade_ready": False}
