"""Compare fixed capital tranches on one identical chronological candidate stream.

Research only. Candidate outcomes are hypothetical until provenance is independently
verified. No broker connection, market data acquisition, or order execution.
"""
import math
from research_settled_cash import simulate_settled_cash

TRANCHES_EUR = (3500, 5000, 7500, 10000)


def compare_tranche_capacity(candidates, *, starting_settled_cash_eur,
                             tranches_eur=TRANCHES_EUR, max_positions=6,
                             settlement_business_days=2, settlement_holidays=(),
                             round_trip_cost_rate=0.005):
    """Strict identity; same candidate ordering and settlement assumptions.

    Capital acceptance/rejection is descriptive. Does not rank realized
    performance, infer returns on rejected candidates or select a best tranche.
    """
    if not isinstance(candidates, list):
        raise ValueError("INVALID_CANDIDATES")
    if not isinstance(tranches_eur, (tuple, list)) or not tranches_eur:
        raise ValueError("INVALID_TRANCHES")
    if any(isinstance(t, bool) or not isinstance(t, (int, float))
           or not math.isfinite(t) or t <= 0 for t in tranches_eur):
        raise ValueError("INVALID_TRANCHES")
    if len(set(float(t) for t in tranches_eur)) != len(tranches_eur):
        raise ValueError("DUPLICATE_TRANCHES")
    results = []
    for tranche in tranches_eur:
        result = simulate_settled_cash(
            candidates, starting_settled_cash_eur=starting_settled_cash_eur,
            tranche_eur=tranche, max_positions=max_positions,
            settlement_business_days=settlement_business_days,
            settlement_holidays=settlement_holidays,
            round_trip_cost_rate=round_trip_cost_rate, require_symbol=True)
        results.append({
            "tranche_eur": tranche,
            "accepted_count": result["accepted_count"],
            "rejected_count": result["rejected_count"],
            "rejection_reasons": result["rejection_reasons"],
            "accepted_candidate_ids": [event["id"] for event in result["events"]
                                       if event["decision"] == "SIMULATED_ACCEPT"],
            "rejected_candidate_ids": [event["id"] for event in result["events"]
                                       if event["decision"] != "SIMULATED_ACCEPT"],
            "cash_after_last_entry_eur": result["cash_after_last_entry_eur"],
            "unsettled_proceeds_eur": result["unsettled_proceeds_eur"],
            "unsettled_proceeds_includes_future_exits": result["unsettled_proceeds_includes_future_exits"],
            "asof_last_entry_date": result["asof_last_entry_date"],
            "future_not_yet_exited_proceeds_eur": result["future_not_yet_exited_proceeds_eur"],
            "exited_but_unsettled_proceeds_eur": result["exited_but_unsettled_proceeds_eur"],
        })
    return {
        "status": "RESEARCH_ONLY_CAPITAL_CAPACITY_COMPARISON",
        "candidate_count": len(candidates),
        "starting_settled_cash_eur": starting_settled_cash_eur,
        "max_positions": max_positions,
        "settlement_business_days_assumption": settlement_business_days,
        "holiday_calendar_coverage_verified": False,
        "symbol_identity_required": True,
        "scenarios": results,
        "best_tranche_identified": False,
        "historical_edge_proven": False,
        "actual_broker_cash_verified": False,
        "trade_ready": False,
        "automatic_orders": False,
    }
