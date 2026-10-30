"""Offline price-only recovery hypothesis benchmark on genuine OHLC rows.

No event timestamp dependency. Uses only trailing closes at decision time.
Every selected entry is next-session open; exit is open after N sessions.
Data supplied by caller; no claim that a historical edge exists.
"""
from math import isfinite
from statistics import mean
from research_swing_historical_event_inputs import validate_daily_bars


def recovery_vs_unconditional(bars_by_symbol, *, horizons=(3, 5, 10, 15),
                              lookback=20, dip_pct=10.0, cost_bps=50):
    if not isinstance(bars_by_symbol, dict) or not bars_by_symbol:
        raise ValueError("missing_price_universe")
    if type(lookback) is not int or lookback < 2:
        raise ValueError("invalid_lookback")
    if type(dip_pct) not in (int, float) or not isfinite(dip_pct) or not 0 < dip_pct < 100:
        raise ValueError("invalid_dip")
    if type(cost_bps) not in (int, float) or not isfinite(cost_bps) or not 0 <= cost_bps <= 1000:
        raise ValueError("invalid_cost")
    if not isinstance(horizons, (tuple, list)) or not horizons or any(
            type(h) is not int or h < 1 for h in horizons):
        raise ValueError("invalid_horizons")
    output = {}
    for h in horizons:
        selected, baseline = [], []
        symbols_with_signals = set()
        for symbol, bars in bars_by_symbol.items():
            if not isinstance(symbol, str) or not symbol:
                raise ValueError("invalid_symbol")
            validate_daily_bars(bars)
            last_selected_exit = -1
            for decision in range(lookback - 1, len(bars) - h - 1):
                # All observations in the lookback window are known by close.
                prior_high = max(b["close"] for b in bars[decision-lookback+1:decision+1])
                drawdown_pct = 100 * (bars[decision]["close"] / prior_high - 1)
                entry_index = decision + 1
                exit_index = entry_index + h
                entry, exit_ = bars[entry_index]["open"], bars[exit_index]["open"]
                net = 100 * (exit_ / entry - 1) - cost_bps / 100
                baseline.append(net)
                if drawdown_pct <= -dip_pct and entry_index > last_selected_exit:
                    selected.append(net)
                    symbols_with_signals.add(symbol)
                    last_selected_exit = exit_index
        output[str(h)] = {
            "signal_trades": len(selected),
            "signal_symbols": len(symbols_with_signals),
            "baseline_observations_overlapping": len(baseline),
            "signal_mean_net_pct": round(mean(selected), 4) if selected else None,
            "baseline_mean_net_pct": round(mean(baseline), 4) if baseline else None,
            "signal_loss_fraction": round(sum(v < 0 for v in selected) / len(selected), 4) if selected else None,
            "signal_min_net_pct": round(min(selected), 4) if selected else None,
            "baseline_not_independent": True,
            "trade_ready": False,
        }
    return {"hypothesis": "trailing_close_drawdown", "dip_pct": dip_pct,
            "lookback": lookback, "cost_bps": cost_bps, "horizons": output,
            "predictive_edge_proven": False, "trade_ready": False}
