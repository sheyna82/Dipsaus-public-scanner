"""Conservative research-only opening auction fill capacity gate.

No historical OHLC bar proves executable liquidity at the opening print.
This gate requires a separately supplied opening-auction volume observation
and applies a fixed maximum participation fraction. It is an upper-bound
capacity screen, NOT a fill guarantee or independent source attestation.
"""
from decimal import Decimal, InvalidOperation


def _d(value):
    if isinstance(value, bool):
        raise ValueError("invalid_liquidity_input")
    try:
        n = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        raise ValueError("invalid_liquidity_input") from None
    if not n.is_finite():
        raise ValueError("invalid_liquidity_input")
    return n


def assess_open_auction_capacity(candidates, *, max_participation_pct=1):
    cap = _d(max_participation_pct)
    if not 0 < cap <= 100:
        raise ValueError("invalid_participation_limit")
    if not isinstance(candidates, (list, tuple)) or not candidates:
        raise ValueError("empty_liquidity_cohort")
    results = {}
    for item in candidates:
        if not isinstance(item, dict):
            raise ValueError("invalid_candidate")
        ticker = item.get("ticker")
        if not isinstance(ticker, str) or not ticker.strip() or ticker in results:
            raise ValueError("duplicate_or_invalid_ticker")
        shares = item.get("planned_shares")
        if isinstance(shares, bool) or not isinstance(shares, int) or shares < 1:
            raise ValueError("invalid_planned_shares")
        volume = _d(item.get("opening_auction_volume"))
        if volume <= 0 or volume != volume.to_integral_value():
            raise ValueError("invalid_opening_auction_volume")
        capacity = int(volume * cap / 100)
        results[ticker] = {
            "planned_shares": shares,
            "opening_auction_volume": str(volume),
            "max_modeled_shares": capacity,
            "capacity_screen_passed": shares <= capacity,
        }
    return {
        "research_only": True, "trade_ready": False,
        "historical_fill_guaranteed": False,
        "source_authenticity_verified": False,
        "opening_auction_volume_required": True,
        "max_participation_pct": str(cap),
        "results": results,
    }
