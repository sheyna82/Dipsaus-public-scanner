"""Research-only causal close-signal/next-open exit policy comparison.

Inputs are session-aligned arrays. This deliberately models ONE trade, not a
portfolio; it cannot establish profitable strategy selection. Daily OHLC cannot
prove a limit-order fill.
"""
from decimal import Decimal

HORIZONS = (3, 5, 10, 15, 20, 30, 40)


def _d(value):
    result = Decimal(str(value))
    if not result.is_finite() or result <= 0:
        raise ValueError("invalid_price_or_cost")
    return result


def compare_exit_policies(opens, closes, *, entry_index=1, entry_budget=3500,
                          cost_bps_per_side=10, horizons=HORIZONS,
                          trailing_drawdown_pct=8, min_hold=3, max_hold=40):
    """Enter at open[entry_index] using a signal known at previous close.

    At close[t], a dynamic exit may be triggered; fill is open[t+1].
    Fixed horizon N exits at open[entry_index+N]. Costs applied to both sides.
    """
    if len(opens) != len(closes) or len(opens) < 5:
        raise ValueError("invalid_sessions")
    op, cl = list(map(_d, opens)), list(map(_d, closes))
    if isinstance(entry_index, bool) or not isinstance(entry_index, int) or entry_index < 1:
        raise ValueError("invalid_entry")
    if not (0 <= cost_bps_per_side < 10000):
        raise ValueError("invalid_cost")
    budget = _d(entry_budget)
    cost = Decimal(str(cost_bps_per_side)) / Decimal(10000)
    if not 0 <= trailing_drawdown_pct < 100 or not 1 <= min_hold <= max_hold:
        raise ValueError("invalid_dynamic_policy")
    if not horizons or any(isinstance(h, bool) or not isinstance(h, int) or h < 1 for h in horizons):
        raise ValueError("invalid_horizon")
    if entry_index + max(max(horizons), max_hold) >= len(op):
        raise ValueError("insufficient_future_sessions")
    entry = op[entry_index] * (1 + cost)
    shares = int(budget // entry)
    if shares == 0:
        raise ValueError("budget_below_one_share")
    spent = entry * shares

    def result(exit_index, reason):
        sell = op[exit_index] * (1 - cost)
        pnl = (sell - entry) * shares
        return {"exit_index": exit_index, "holding_sessions": exit_index-entry_index,
                "reason": reason, "shares": shares,
                "net_pnl": str(pnl.quantize(Decimal("0.01"))),
                "return_on_budget_pct": str((pnl/budget*100).quantize(Decimal("0.0001")))}

    fixed = {str(h): result(entry_index+h, "fixed_horizon") for h in horizons}
    high = cl[entry_index-1]
    chosen = entry_index+max_hold
    reason = "maximum_holding_period"
    for t in range(entry_index, entry_index+max_hold):
        high = max(high, cl[t])
        drawdown = (high-cl[t])/high*100
        held_on_next_open = t+1-entry_index
        if held_on_next_open >= min_hold and drawdown >= Decimal(str(trailing_drawdown_pct)):
            chosen, reason = t+1, "trailing_close_drawdown_next_open"
            break
    return {"research_only": True, "trade_ready": False,
            "signal_assumed_known_before_entry": True,
            "fill_model": "next_session_open_with_symmetric_cost_bps",
            "unspent_cash": str((budget-spent).quantize(Decimal("0.01"))),
            "fixed": fixed, "dynamic": result(chosen, reason),
            "warning": "No corporate-action adjustment, event gap, FX, portfolio ledger or independently verified data."}
