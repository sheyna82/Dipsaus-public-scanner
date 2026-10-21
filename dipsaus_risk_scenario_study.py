"""Offline scenario study for technical support pressure.

Synthetic paths are unit-test fixtures, not historical validation or trading
performance evidence. No live feeds, alerts, or execution.
"""
from dipsaus_optional_risk_research import assess_risk, assess_structure_pressure
from dipsaus_risk_profit_research import combine_research


def study_scenario(bars, entry, observed_prices, profit_status="NO_PROFIT_CONTEXT"):
    """Assess a fixed support reference across an observed price sequence.

    Reference is frozen before subsequent observations: no future data leakage.
    This is NOT a time-confirmed break or real trade simulation.
    """
    context = assess_risk(bars, entry)
    if context is None or not isinstance(observed_prices, (list, tuple)) or not observed_prices:
        return None
    observations = []
    for price in observed_prices:
        pressure = assess_structure_pressure(context, price)
        if pressure is None:
            return None
        joint = combine_research(pressure, {"status": profit_status})
        if joint is None:
            return None
        observations.append({"observed_price": price, "risk_state": pressure["state"],
                             "joint_review": joint["joint_review"],
                             "sell_recommendation": False,
                             "notify": False})
    return {"support_reference": context["recent_support"],
            "atr_reference": context["atr"],
            "observations": observations,
            "synthetic_scenario_only": True,
            "historically_validated": False,
            "trade_ready": False,
            "automatic_sell": False,
            "stop_order_created": False}
