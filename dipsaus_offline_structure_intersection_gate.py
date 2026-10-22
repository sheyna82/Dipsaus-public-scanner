"""Fixed joint factor diagnostics on actual chronological event rows; research only."""
from dipsaus_offline_structure_regime_diagnostic import evaluate_structure_regime


def evaluate_structure_intersections(stock, benchmark, *, min_test=10):
    base = evaluate_structure_regime(stock, benchmark, min_test=min_test)
    if base.get("status") != "EXPLORATORY_STRUCTURE_REGIME_DIAGNOSTIC":
        return {"status": "DATA_BLOCKED", "reason": base.get("reason", "invalid_history"),
                "test_events": base.get("test_events"), "trade_ready": False}
    rows = base.get("test_rows")
    if not isinstance(rows, list) or len(rows) != base["test_events"]:
        return {"status": "DATA_BLOCKED", "reason": "joint_event_rows_not_exposed", "trade_ready": False}

    def metrics(group):
        if not group:
            return None
        return {"events": len(group),
                "mean_net_return_pct": round(sum(r["terminal_return_net_pct"] for r in group)/len(group), 5),
                "mean_adverse_excursion_pct": round(sum(r["max_adverse_excursion_pct"] for r in group)/len(group), 5),
                "severe_adverse_rate_pct": round(100*sum(r["max_adverse_excursion_pct"] <= -3 for r in group)/len(group), 3),
                "winning_events": sum(r["terminal_return_net_pct"] > 0 for r in group)}

    combinations = {
        "atr_and_structure": ("atr_expanding", "structure_above_20d_mean"),
        "atr_and_market": ("atr_expanding", "market_20d_positive"),
        "atr_structure_market": ("atr_expanding", "structure_above_20d_mean", "market_20d_positive"),
    }
    factors = {}
    for name, fields in combinations.items():
        selected = [r for r in rows if all(r[field] for field in fields)]
        skipped = [r for r in rows if not all(r[field] for field in fields)]
        factors[name] = {"selected": metrics(selected), "skipped": metrics(skipped),
                         "missed_winning_events": sum(r["terminal_return_net_pct"] > 0 for r in skipped)}
    regime_groups = {}
    for label, market_up in (("market_20d_positive", True), ("market_20d_nonpositive", False)):
        regime_rows = [r for r in rows if r["market_20d_positive"] is market_up]
        atr_structure = [r for r in regime_rows if r["atr_expanding"] and r["structure_above_20d_mean"]]
        rejected = [r for r in regime_rows if not (r["atr_expanding"] and r["structure_above_20d_mean"])]
        regime_groups[label] = {"baseline": metrics(regime_rows),
                                "atr_structure_selected": metrics(atr_structure),
                                "atr_structure_rejected": metrics(rejected),
                                "missed_winning_events": sum(r["terminal_return_net_pct"] > 0 for r in rejected)}
    # Ten-session outcomes overlap when signals occur fewer than ten sessions apart.
    # This is a dependence diagnostic, not an independence correction.
    index = {bar["date"]: i for i, bar in enumerate(stock)}
    positions = sorted(index[r["signal_date"]] for r in rows)
    overlap_pairs = sum(
        positions[j] - positions[i] < 10
        for i in range(len(positions))
        for j in range(i + 1, len(positions))
        if positions[j] - positions[i] < 10
    )
    nonoverlapping_greedy = 0
    last = -10
    for position in positions:
        if position - last >= 10:
            nonoverlapping_greedy += 1
            last = position
    return {"status": "EXPLORATORY_JOINT_FACTOR_DIAGNOSTIC",
            "market_regime_diagnostics": regime_groups,
            "dependence_diagnostic": {"test_signal_dates": [r["signal_date"] for r in rows],
                "overlapping_event_pairs": overlap_pairs,
                "greedy_nonoverlapping_event_count": nonoverlapping_greedy,
                "horizon_sessions": 10, "independent_observations_claimed": False},
            "test_events": len(rows), "baseline_test": metrics(rows), "factors": factors,
            "combinations_predeclared": True, "independent_untouched_holdout": False,
            "predictive_edge_proven": False, "trade_ready": False}
