"""Research-only conservative limit-order fill eligibility.

Inspired by order execution simulation concepts, not copied from Backtrader.
A daily OHLC range can only show that a limit price was *touched*, not that
our order was filled. Avoid same-bar close-derived limit placement.
"""
from decimal import Decimal, InvalidOperation


def _d(value):
    if isinstance(value, bool):
        raise ValueError("invalid_limit_input")
    try:
        result = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        raise ValueError("invalid_limit_input") from None
    if not result.is_finite() or result <= 0:
        raise ValueError("invalid_limit_input")
    return result


def assess_limit_fill(side, limit_price, session_open, session_high,
                      session_low, *, order_submitted_before_open=False):
    if side not in ("buy", "sell"):
        raise ValueError("invalid_side")
    limit, opening, high, low = map(
        _d, (limit_price, session_open, session_high, session_low))
    if not low <= opening <= high:
        raise ValueError("invalid_ohlc")
    if order_submitted_before_open is not True:
        raise ValueError("preopen_order_timestamp_required")
    if side == "buy":
        marketable_at_open = opening <= limit
        touched = low <= limit
        conservative = opening < limit or low < limit
    else:
        marketable_at_open = opening >= limit
        touched = high >= limit
        conservative = opening > limit or high > limit
    return {
        "research_only": True,
        "trade_ready": False,
        "side": side,
        "limit_touched": bool(touched),
        "marketable_at_open": bool(marketable_at_open),
        "strictly_crossed_limit": bool(conservative),
        "fill_confirmed": False,
        "execution_price_known": False,
        "daily_bar_cannot_prove_fill": True,
    }
