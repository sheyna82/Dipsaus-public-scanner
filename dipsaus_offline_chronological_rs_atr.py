"""Chronological RS/ATR gate diagnostics without holdout retuning.

Thresholds are fixed from training events only, and each feature's
direction is fixed in advance. This is NOT an independent untouched
holdout: the hypotheses were inspired by earlier observations.
"""
from datetime import date
from statistics import median
from dipsaus_offline_frozen_rs_atr import annotate_frozen_events_rs_atr


def chronological_rs_atr_diagnostic(stock, benchmark, *, horizon=10,
                                   train_fraction=0.7, embargo_sessions=10,
                                   min_train=15, min_test=10):
    result = annotate_frozen_events_rs_atr(stock, benchmark, horizon=horizon)
    if result.get("status") != "EXPLORATORY_FROZEN_RS_ATR":
        return {"status": "DATA_BLOCKED", "reason": result.get("reason", "invalid_history"),
                "trade_ready": False}
    if (not isinstance(train_fraction, (int, float)) or isinstance(train_fraction, bool)
            or not 0.5 <= train_fraction <= 0.85 or type(embargo_sessions) is not int
            or embargo_sessions < horizon or type(min_train) is not int or min_train < 2
            or type(min_test) is not int or min_test < 2):
        return {"status": "DATA_BLOCKED", "reason": "invalid_split_parameters", "trade_ready": False}
    split = int(len(stock) * train_fraction)
    if split <= 21 or split >= len(stock):
        return {"status": "DATA_BLOCKED", "reason": "invalid_split", "trade_ready": False}
    date_index = {bar["date"]: i for i, bar in enumerate(stock)}
    train = [r for r in result["rows"] if date_index[r["signal_date"]] + horizon < split]
    test = [r for r in result["rows"] if date_index[r["signal_date"]] >= split + embargo_sessions]
    if len(train) < min_train or len(test) < min_test:
        return {"status": "DATA_BLOCKED", "reason": "insufficient_split_events",
                "train_events": len(train), "test_events": len(test), "trade_ready": False}

    def metrics(rows):
        n = len(rows)
        if not n:
            return None
        return {"events": n,
                "mean_net_return_pct": round(sum(r["terminal_return_net_pct"] for r in rows) / n, 5),
                "mean_adverse_excursion_pct": round(sum(r["max_adverse_excursion_pct"] for r in rows) / n, 5),
                "severe_adverse_rate_pct": round(100 * sum(r["max_adverse_excursion_pct"] <= -3 for r in rows) / n, 3),
                "positive_terminal_rate_pct": round(100 * sum(r["terminal_return_net_pct"] > 0 for r in rows) / n, 3)}

    factors = {}
    for name, field in (("rs", "relative_strength_20d_pct_points"),
                        ("atr", "atr_14d_pct")):
        cutoff = median(r[field] for r in train)
        # Pre-specified directions: stronger RS and lower ATR for a less
        # volatile recovery candidate. No direction chosen from test outcomes.
        selected = [r for r in test if (r[field] > cutoff if name == "rs" else r[field] <= cutoff)]
        skipped = [r for r in test if r not in selected]
        factors[name] = {"train_median_cutoff": round(cutoff, 6),
                         "direction": "above" if name == "rs" else "at_or_below",
                         "selected": metrics(selected), "skipped": metrics(skipped),
                         "missed_winning_events": sum(r["terminal_return_net_pct"] > 0 for r in skipped),
                         "coverage_pct": round(100 * len(selected) / len(test), 3)}
    return {"status": "EXPLORATORY_CHRONOLOGICAL_DIAGNOSTIC",
            "split_date": stock[split]["date"], "train_events": len(train),
            "test_events": len(test), "embargo_sessions": embargo_sessions,
            "baseline_test": metrics(test), "factors": factors,
            "hypothesis_independently_preregistered": False,
            "independent_untouched_holdout": False,
            "source_verified": False, "predictive_edge_proven": False, "trade_ready": False}
