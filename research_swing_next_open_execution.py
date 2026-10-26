"""Research-only next-session exit execution model.

A completed close can trigger an exit decision, but cannot also guarantee
execution at that already observed close. Sell at the *next* session open
provided explicitly by the caller. Does not model gaps beyond the supplied
open or intraday liquidity; no live trading integration.
"""
from decimal import Decimal, InvalidOperation


def _d(value):
    if isinstance(value, bool):
        raise ValueError("invalid_price_or_cost")
    try:
        number = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        raise ValueError("invalid_price_or_cost") from None
    if not number.is_finite():
        raise ValueError("invalid_price_or_cost")
    return number


def simulate_next_open_exit(entry_price, closes, next_opens, capital, *,
                            horizon=5, target_pct=None, trailing_pct=None,
                            spread_bps=0, slippage_bps=0, commission_bps=0):
    """Fixed-horizon/close-trigger decision, next-session open exit.

    close[i] is known only after session i. next_opens[i] is the following
    session's open. The caller must independently validate chronological
    source timestamps and corporate-action-adjusted price consistency.
    """
    if isinstance(horizon, bool) or horizon not in (3, 5, 10):
        raise ValueError("invalid_horizon")
    if len(closes) < horizon or len(next_opens) < horizon:
        raise ValueError("incomplete_next_open_horizon")
    entry, cash = _d(entry_price), _d(capital)
    spread, slip, fee = map(_d, (spread_bps, slippage_bps, commission_bps))
    if entry <= 0 or cash <= 0 or any(v < 0 for v in (spread, slip, fee)):
        raise ValueError("invalid_execution_inputs")
    if spread / 2 + slip >= 10000 or fee >= 10000:
        raise ValueError("invalid_execution_costs")
    prices = [_d(x) for x in closes[:horizon]]
    opens = [_d(x) for x in next_opens[:horizon]]
    if any(x <= 0 for x in prices + opens):
        raise ValueError("invalid_price")
    target = None if target_pct is None else _d(target_pct)
    trail = None if trailing_pct is None else _d(trailing_pct)
    if target is not None and target <= 0:
        raise ValueError("invalid_target")
    if trail is not None and not 0 < trail < 100:
        raise ValueError("invalid_trailing")
    buy = entry * (1 + (spread / 2 + slip) / 10000)
    shares = int(cash / (buy * (1 + fee / 10000)))
    if shares < 1:
        raise ValueError("insufficient_capital")
    peak = entry
    day, reason = horizon, "time_next_open"
    for i, close in enumerate(prices, 1):
        peak = max(peak, close)
        if target is not None and close >= entry * (1 + target / 100):
            day, reason = i, "target_next_open"
            break
        if trail is not None and peak > entry and close <= peak * (1 - trail / 100):
            day, reason = i, "trailing_next_open"
            break
    sell = opens[day - 1] * (1 - (spread / 2 + slip) / 10000)
    pnl = shares * (sell * (1 - fee / 10000) - buy * (1 + fee / 10000))
    return {"research_only": True, "trade_ready": False,
            "exit_decision_session": day,
            "exit_execution": "following_session_open",
            "exit_reason": reason, "shares": shares,
            "net_pnl": str(pnl.quantize(Decimal("0.01"))),
            "net_return_on_allocated_capital_pct":
                str((pnl / cash * 100).quantize(Decimal("0.0001")))}
