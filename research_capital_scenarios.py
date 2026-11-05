"""Offline capital-allocation scenario arithmetic; no broker link or trading decisions."""
import math


def compare_capital_scenarios(*, budget_eur, invested_eur, free_room_eur,
                              observed_positions, max_positions=6,
                              tranche_sizes=(3500, 5000, 7500, 10000)):
    """Illustrative capacity only; free room is NOT authenticated cash."""
    def amount(value):
        return (isinstance(value, (int, float)) and not isinstance(value, bool)
                and math.isfinite(value) and value >= 0)
    if not all(amount(v) for v in (budget_eur, invested_eur, free_room_eur)):
        raise ValueError("INVALID_CAPITAL_INPUT")
    if budget_eur <= 0 or not isinstance(max_positions, int) or isinstance(max_positions, bool) or max_positions < 1:
        raise ValueError("INVALID_CAPITAL_LIMIT")
    if not isinstance(observed_positions, int) or isinstance(observed_positions, bool) or observed_positions < 0:
        raise ValueError("INVALID_POSITION_COUNT")
    if not isinstance(tranche_sizes, (tuple, list)) or not tranche_sizes or any(not amount(t) or t <= 0 for t in tranche_sizes):
        raise ValueError("INVALID_TRANCHE_SIZES")
    slots = max(0, max_positions - observed_positions)
    scenarios = []
    for tranche in tranche_sizes:
        total = tranche * slots
        scenarios.append({
            "tranche_eur": float(tranche),
            "illustrative_new_positions": slots,
            "illustrative_new_allocation_eur": round(total, 2),
            "within_budget_if_existing_positions_unchanged": invested_eur + total <= budget_eur,
            "within_displayed_free_room_only": total <= free_room_eur,
            "risk_adjusted": False,
            "trade_ready": False,
        })
    return {
        "status": "RESEARCH_ONLY_CAPITAL_SCENARIOS",
        "budget_eur": round(budget_eur, 2),
        "invested_eur": round(invested_eur, 2),
        "displayed_free_room_eur": round(free_room_eur, 2),
        "observed_position_count_claim": observed_positions,
        "max_positions": max_positions,
        "illustrative_unfilled_slots": slots,
        "scenarios": scenarios,
        "cash_authenticated": False,
        "broker_complete_authenticated": False,
        "risk_capacity_verified": False,
        "allocation_recommendation": None,
        "trade_ready": False,
        "automatic_orders": False,
    }
