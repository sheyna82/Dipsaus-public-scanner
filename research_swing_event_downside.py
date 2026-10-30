"""Offline downside outcome labels for event research; not a predictive model."""
from math import isfinite

def event_downside_outcomes(bars, *, known_session_index, horizons=(3, 5, 10, 15),
                            loss_thresholds_pct=(5, 10), cost_bps_roundtrip=30,
                            slippage_bps_per_side=10):
    """Signal at known session close; entry next open; exit after N sessions.

    Worst intratrade low measures adverse excursion; never use it as an
    executable stop fill. Return labels only, not future-aware entry scores.
    """
    i = known_session_index
    if type(i) is not int or i < 0 or i + 2 >= len(bars):
        raise ValueError("invalid_known_session_index")
    if any(type(h) is not int or h < 1 for h in horizons):
        raise ValueError("invalid_horizons")
    if any(not isinstance(t, (int, float)) or not isfinite(t) or t <= 0
           for t in loss_thresholds_pct):
        raise ValueError("invalid_thresholds")
    if not 0 <= cost_bps_roundtrip <= 1000 or not 0 <= slippage_bps_per_side <= 500:
        raise ValueError("invalid_costs")
    for row in bars:
        if any(not isinstance(row[k], (int, float)) or not isfinite(row[k]) or row[k] <= 0
               for k in ("open", "low")):
            raise ValueError("invalid_prices")
    entry_index = i + 1
    entry = bars[entry_index]["open"] * (1 + slippage_bps_per_side / 10000)
    outcomes = []
    for horizon in horizons:
        exit_index = entry_index + horizon
        if exit_index >= len(bars):
            continue
        exit_price = bars[exit_index]["open"] * (1 - slippage_bps_per_side / 10000)
        net_return_pct = 100 * (exit_price / entry - 1) - cost_bps_roundtrip / 100
        worst_low = min(row["low"] for row in bars[entry_index:exit_index])
        adverse_excursion_pct = 100 * (worst_low / entry - 1)
        outcomes.append({
            "horizon": horizon,
            "entry_index": entry_index,
            "exit_index": exit_index,
            "net_return_pct": round(net_return_pct, 4),
            "net_loss": net_return_pct < 0,
            "worst_intratrade_excursion_pct": round(adverse_excursion_pct, 4),
            "adverse_threshold_hits": {str(t): adverse_excursion_pct <= -t
                                       for t in loss_thresholds_pct},
            "trade_ready": False,
        })
    return outcomes
