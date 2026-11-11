"""Research-only deterministic net-P&L simulator for short swing exits.

Synthetic/offline use only. No broker, price feed, orders, or live alerts.
Returns are based on entry/exit execution prices after modeled spread and
slippage, with per-side percentage commissions.
"""
from decimal import Decimal, InvalidOperation


def _d(value, name):
    if isinstance(value, bool):
        raise ValueError(name + "_invalid")
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError):
        raise ValueError(name + "_invalid") from None
    if not result.is_finite():
        raise ValueError(name + "_invalid")
    return result


def simulate_swing(entry_price, daily_closes, capital, *,
                   horizon=5, spread_bps=0, slippage_bps=0,
                   commission_bps=0, target_pct=None,
                   trailing_pct=None):
    """Compare a time exit, optional profit target and trailing profit protection.

    Each element of daily_closes is a completed trading session close.
    Target/trailing triggers are checked on closes, not assumed intraday fills.
    Entry pays half the spread; exit loses half the spread. Both sides incur
    slippage and commissions. No fractional shares.
    """
    entry = _d(entry_price, "entry_price")
    cash = _d(capital, "capital")
    spread = _d(spread_bps, "spread_bps")
    slip = _d(slippage_bps, "slippage_bps")
    fee = _d(commission_bps, "commission_bps")
    if entry <= 0 or cash <= 0 or any(x < 0 for x in (spread, slip, fee)):
        raise ValueError("invalid_execution_inputs")
    if spread / 2 + slip >= 10000 or fee >= 10000:
        raise ValueError("invalid_execution_costs")
    if isinstance(horizon, bool) or horizon not in (3, 5, 10):
        raise ValueError("invalid_horizon")
    if len(daily_closes) < horizon:
        raise ValueError("incomplete_horizon")
    closes = [_d(v, "daily_close") for v in daily_closes[:horizon]]
    if any(v <= 0 for v in closes):
        raise ValueError("invalid_daily_close")
    target = None if target_pct is None else _d(target_pct, "target_pct")
    trail = None if trailing_pct is None else _d(trailing_pct, "trailing_pct")
    if target is not None and target <= 0:
        raise ValueError("invalid_target")
    if trail is not None and not (0 < trail < 100):
        raise ValueError("invalid_trailing")
    buy = entry * (1 + (spread / 2 + slip) / 10000)
    shares = int(cash / (buy * (1 + fee / 10000)))
    if shares < 1:
        raise ValueError("insufficient_capital")
    peak = entry
    reason = "time"
    exit_day = horizon
    for day, close in enumerate(closes, 1):
        peak = max(peak, close)
        if target is not None and close >= entry * (1 + target / 100):
            reason, exit_day = "target_close", day
            break
        if trail is not None and peak > entry and close <= peak * (1 - trail / 100):
            reason, exit_day = "trailing_close", day
            break
    sell = closes[exit_day - 1] * (1 - (spread / 2 + slip) / 10000)
    entry_cost = buy * shares * (1 + fee / 10000)
    exit_proceeds = sell * shares * (1 - fee / 10000)
    pnl = exit_proceeds - entry_cost
    return {"research_only": True, "trade_ready": False,
            "horizon": horizon, "exit_session": exit_day,
            "exit_reason": reason, "shares": shares,
            "net_pnl": str(pnl.quantize(Decimal("0.01"))),
            "net_return_on_allocated_capital_pct":
                str((pnl / cash * 100).quantize(Decimal("0.0001"))),
            "unused_cash": str((cash - entry_cost).quantize(Decimal("0.01")))}
