"""Leakage-aware forward-return research for observed notification cases.

Research only. Prices are externally supplied daily bars; no orders, alerts or
automatic market-data retrieval. Missing outcomes remain missing.
"""
from datetime import datetime, timezone

HORIZONS = (3, 5, 10, 20)

def forward_returns(signal_utc, bars, horizons=HORIZONS, round_trip_cost_bps=30):
    """Use the first *later* trading session's open as entry.

    Each bar: {'date':'YYYY-MM-DD', 'open':positive, 'close':positive}.
    Signal timestamps must be UTC-aware. Without exchange-calendar confirmation
    and broker quotes these are illustrative proxy returns, not trade P&L.
    """
    if not isinstance(signal_utc, datetime) or signal_utc.tzinfo is None:
        raise ValueError("signal_requires_timezone_aware_timestamp")
    if not 0 <= round_trip_cost_bps <= 1000:
        raise ValueError("invalid_cost_assumption")
    day = signal_utc.astimezone(timezone.utc).date().isoformat()
    if any(not isinstance(b.get("date"), str) or
           not isinstance(b.get("open"), (int, float)) or
           not isinstance(b.get("close"), (int, float)) or
           b["open"] <= 0 or b["close"] <= 0 for b in bars):
        raise ValueError("invalid_bars")
    dates = [b["date"] for b in bars]
    if dates != sorted(set(dates)):
        raise ValueError("bars_must_be_unique_and_sorted")
    future = [b for b in bars if b["date"] > day]
    if not future:
        return {h: None for h in horizons}
    entry = future[0]["open"]
    result = {}
    for h in horizons:
        if not isinstance(h, int) or h < 1:
            raise ValueError("invalid_horizon")
        if len(future) <= h:
            result[h] = None
            continue
        exit_price = future[h]["close"]
        result[h] = {
            "gross_return_pct": round(100 * (exit_price / entry - 1), 4),
            "net_proxy_return_pct": round(100 * (exit_price / entry - 1) - round_trip_cost_bps / 100, 4),
            "entry_date": future[0]["date"],
            "exit_date": future[h]["date"],
            "execution_verified": False,
            "research_only": True,
        }
    return result
