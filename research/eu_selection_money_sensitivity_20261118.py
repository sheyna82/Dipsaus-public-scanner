"""Offline gross-move sensitivity for a fixed EUR net-profit threshold.

Illustrative friction scenarios only. No bid/ask or broker fee attestation,
no security recommendations, orders or notifications.
"""
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

def required_gross_move(*, allocation_eur, net_goal_eur="150",
                        round_trip_fixed_eur="0", round_trip_variable_pct="0"):
    blocked={"status":"BLOCKED","trade_ready":False,"notify":False,"automatic_orders":False}
    try:
        values=(allocation_eur,net_goal_eur,round_trip_fixed_eur,round_trip_variable_pct)
        if any(isinstance(x,bool) for x in values):
            raise ValueError("boolean input")
        capital,goal,fixed,variable=(Decimal(str(x)) for x in values)
        if not all(x.is_finite() for x in (capital,goal,fixed,variable)):
            raise ValueError("nonfinite")
        if capital<=0 or goal<=0 or fixed<0 or not 0<=variable<100:
            raise ValueError("range")
        # Variable round-trip friction is a percentage of allocated capital,
        # not of gross sale proceeds. Explicit assumption, not execution quote.
        friction=fixed+capital*variable/Decimal("100")
        gross_needed=goal+friction
        pct=gross_needed/capital*Decimal("100")
    except (InvalidOperation,ValueError,TypeError,OverflowError):
        return {**blocked,"blocks":["SCENARIO_INPUT_INVALID"]}
    fmt=lambda x:str(x.quantize(Decimal("0.01"),rounding=ROUND_HALF_UP))
    return {**blocked,"status":"ILLUSTRATIVE_RESEARCH_ONLY",
            "allocation_eur":fmt(capital),"net_goal_eur":fmt(goal),
            "assumed_round_trip_friction_eur":fmt(friction),
            "required_gross_profit_eur":fmt(gross_needed),
            "required_gross_move_pct":fmt(pct),
            "assumptions":"Fixed costs plus round-trip variable percent of initial allocation; no actual spreads, FX or slippage verified."}
