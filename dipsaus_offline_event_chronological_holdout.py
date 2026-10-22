"""Research-only strict chronological holdout for completed OHLCV bars.

The existing recovery rule is frozen. No parameter fitting, no alerts, no trades.
Train/test split is based on bar order; embargo prevents pre-split signals from
being evaluated as test signals. This is diagnostic, not proof of an edge.
"""
from dipsaus_offline_ohlcv_features import _valid
from dipsaus_offline_event_history_outcomes import evaluate_daily_event_history


def chronological_holdout(rows, *, train_fraction=0.7, horizon=10,
                          fee_bps_each_side=10):
    if not _valid(rows) or type(train_fraction) not in (float, int) or not 0.5 <= train_fraction <= 0.85:
        return {"status": "DATA_BLOCKED", "reason": "invalid_input",
                "predictive_edge_proven": False, "trade_ready": False}
    if type(horizon) is not int or not 1 <= horizon <= 30:
        return {"status": "DATA_BLOCKED", "reason": "invalid_horizon",
                "predictive_edge_proven": False, "trade_ready": False}
    if type(fee_bps_each_side) not in (int, float) or not 0 <= fee_bps_each_side <= 100:\n        return {"status": "DATA_BLOCKED", "reason": "invalid_cost",\n                "predictive_edge_proven": False, "trade_ready": False}\n    split = int(len(rows) * train_fraction)
    # To compute a test signal at split, allow pre-split feature lookback,
    # but never count pre-split signals or use a future test bar for training.
    test_start = max(0, split - 21)
    train_rows = rows[:split]
    test_rows = rows[test_start:]
    train = evaluate_daily_event_history(train_rows, horizon=horizon,
                                         fee_bps_each_side=fee_bps_each_side)
    test = evaluate_daily_event_history(test_rows, horizon=horizon,
                                        fee_bps_each_side=fee_bps_each_side)
    if train["status"] != "DESCRIPTIVE_HISTORY" or test["status"] != "DESCRIPTIVE_HISTORY":
        return {"status": "DATA_BLOCKED", "reason": "invalid_subhistory",
                "predictive_edge_proven": False, "trade_ready": False}
    # With 21 lookback bars, the first test signal is at index split.
    test_outcomes = [o for o in test["outcomes"] if o["signal_date"] >= rows[split]["date"]]
    def summary(outcomes):
        n = len(outcomes)
        return {"count": n,
                "mean_net_pct": round(sum(o["terminal_return_net_pct"] for o in outcomes) / n, 5) if n else None,
                "positive_count": sum(o["terminal_return_net_pct"] > 0 for o in outcomes),
                "severe_intraperiod_drawdown_count":
                    sum(o["severe_intraperiod_drawdown"] for o in outcomes)}
    return {"status": "DESCRIPTIVE_CHRONOLOGICAL_SPLIT",
            "train_end_date": rows[split - 1]["date"],
            "test_start_date": rows[split]["date"],
            "train": summary(train["outcomes"]),
            "test": summary(test_outcomes),
            "test_signal_count_sufficient": len(test_outcomes) >= 30,\n            "minimum_test_signals_for_screening": 30,\n            "sample_warning": ("INSUFFICIENT_TEST_SIGNALS" if len(test_outcomes) < 30\n                               else "DESCRIPTIVE_ONLY"),\n            "rule_frozen": True, "parameter_tuning_performed": False,
            "test_set_independent_of_development": False,
            "predictive_edge_proven": False, "trade_ready": False}
