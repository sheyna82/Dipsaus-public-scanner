"""Fixed, non-optimized intersections of previously defined structure/regime flags.

Purely exploratory: no threshold search and no live-trading integration.
"""
from dipsaus_offline_structure_regime_diagnostic import evaluate_structure_regime


def evaluate_structure_intersections(stock, benchmark, *, min_test=10):
    base = evaluate_structure_regime(stock, benchmark, min_test=min_test)
    if base.get("status") != "EXPLORATORY_STRUCTURE_REGIME_DIAGNOSTIC":
        return {"status": "DATA_BLOCKED", "reason": base.get("reason", "invalid_history"),
                "test_events": base.get("test_events"), "trade_ready": False}
    # The parent module returns aggregate metrics, not event-level classifications.
    # Do not infer intersections from marginal counts: they are mathematically
    # insufficient to reconstruct overlap and would fabricate observations.
    return {"status": "DATA_BLOCKED", "reason": "joint_event_rows_not_exposed",
            "parent_status": base["status"], "test_events": base["test_events"],
            "required_fields": ["signal_date", "atr_expanding",
                                "structure_above_20d_mean", "market_20d_positive",
                                "terminal_return_net_pct", "max_adverse_excursion_pct"],
            "predictive_edge_proven": False, "trade_ready": False}
