"""Offline, research-only execution assumption scenarios.

No broker simulation, partial fills, intrabar ordering, market data or orders.
A candle's high/low only establishes that a price was touched, not that a
real order was filled. All prices and fees are hypothetical.
"""

import math


def _price(value):
    if type(value) not in (int, float) or not math.isfinite(value) or value <= 0:
        raise ValueError("invalid_price")
    return float(value)


def compare_execution_assumptions(
    *,
    signal_close,
    next_open,
    next_high,
    next_low,
    target_limit,
    spread_bps=0,
    fee_bps=0,
):
    """Compare optimistic close fill with next-open entry and limit touch.

    Assumes a long position, a buy at the next open with full quoted spread
    as a conservative adjustment, and a target sell limit considered only
    after the next open. A touched limit is NOT an independently verified fill.
    """
    close = _price(signal_close)
    opened = _price(next_open)
    high = _price(next_high)
    low = _price(next_low)
    target = _price(target_limit)
    if low > min(opened, high) or high < max(opened, low):
        raise ValueError("inconsistent_candle")
    for value in (spread_bps, fee_bps):
        if type(value) not in (int, float) or not math.isfinite(value) or not 0 <= value < 10000:
            raise ValueError("invalid_cost")
    cost = float(fee_bps) / 10000
    spread = float(spread_bps) / 10000
    assumed_entry = opened * (1 + spread)
    limit_touched = high >= target
    optimistic_net = ((target * (1 - cost)) / (close * (1 + cost)) - 1) * 100
    next_open_net_if_filled = (
        ((target * (1 - cost)) / (assumed_entry * (1 + cost)) - 1) * 100
        if limit_touched else None
    )
    return {
        "optimistic_close_to_target_net_pct": round(optimistic_net, 6),
        "next_open_to_target_net_pct_if_filled": (
            round(next_open_net_if_filled, 6)
            if next_open_net_if_filled is not None else None
        ),
        "limit_price_touched": limit_touched,
        "fill_verified": False,
        "intrabar_sequence_verified": False,
        "partial_fills_modelled": False,
        "trade_ready": False,
    }
