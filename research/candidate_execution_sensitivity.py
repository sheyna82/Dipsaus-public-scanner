"""Conservative research-only entry execution sensitivity, no broker actions.

Inputs are historical OHLC bars and a signal bar index. Enter at next open,
charge explicit adverse slippage, and exit at horizon close. Reject illiquid
or malformed records; do not pretend fills are guaranteed.
"""
import math

def execution_sensitivity(bars, signal_index, *, horizon=10, cost_bps=50,
                          adverse_entry_bps=(0, 10, 25, 50),
                          min_entry_dollar_volume=1_000_000):
    if not isinstance(signal_index, int) or isinstance(signal_index, bool) or signal_index < 0:
        raise ValueError("INVALID_SIGNAL_INDEX")
    if not isinstance(horizon, int) or isinstance(horizon, bool) or horizon < 1:
        raise ValueError("INVALID_HORIZON")
    if signal_index + horizon >= len(bars):
        return {"status": "INSUFFICIENT_FUTURE_BARS", "trade_ready": False}
    if not isinstance(cost_bps, (int, float)) or not math.isfinite(cost_bps) or cost_bps < 0:
        raise ValueError("INVALID_COST")
    entry = bars[signal_index + 1]
    exit_bar = bars[signal_index + horizon]
    for row in (entry, exit_bar):
        if not isinstance(row, dict):
            raise ValueError("INVALID_BAR")
        for field in ("open", "close"):
            v = row.get(field)
            if not isinstance(v, (int, float)) or isinstance(v, bool) or not math.isfinite(v) or v <= 0:
                raise ValueError("INVALID_PRICE")
    # Signal-session OHLCV is known after its close, before next-open entry.
    signal_bar = bars[signal_index]
    if not isinstance(signal_bar, dict):
        raise ValueError("INVALID_SIGNAL_BAR")
    signal_close = signal_bar.get("close")
    if not isinstance(signal_close, (int, float)) or isinstance(signal_close, bool) or not math.isfinite(signal_close) or signal_close <= 0:
        raise ValueError("INVALID_SIGNAL_CLOSE")
    volume = signal_bar.get("volume")
    if not isinstance(volume, (int, float)) or isinstance(volume, bool) or not math.isfinite(volume) or volume < 0:
        return {"status": "MISSING_ENTRY_VOLUME", "trade_ready": False}
    dollar_volume = signal_close * volume
    if dollar_volume < min_entry_dollar_volume:
        return {"status": "INSUFFICIENT_ENTRY_LIQUIDITY", "trade_ready": False,
                "entry_dollar_volume": round(dollar_volume, 2)}
    scenarios = []
    for bps in adverse_entry_bps:
        if not isinstance(bps, (int, float)) or isinstance(bps, bool) or not math.isfinite(bps) or bps < 0:
            raise ValueError("INVALID_SLIPPAGE")
        filled_entry = entry["open"] * (1 + bps / 10000)
        net = 100 * (exit_bar["close"] / filled_entry - 1) - cost_bps / 100
        scenarios.append({"adverse_entry_bps": bps, "net_return_pct": round(net, 4)})
    return {"status": "DESCRIPTIVE_EXECUTION_SENSITIVITY", "trade_ready": False,
            "entry_dollar_volume": round(dollar_volume, 2),
            "liquidity_observation": "signal_session_close_times_volume",
            "liquidity_known_before_next_open": True,
            "horizon_sessions": horizon,
            "cost_bps": cost_bps, "scenarios": scenarios,
            "limitations": ["Historical next-open assumption; actual fill not guaranteed",
                            "Signal-session close and volume known before next-open entry; historical bars still unverified",
                            "No spread, order-book, partial-fill, FX or exit-slippage model",
                            "Not an independent out-of-sample trading validation"]}
