"""Offline descriptive feature extraction from canonical daily OHLCV.

Signals are computed only from current/past rows. Severe outcome labels are
intentionally absent: they require a separately defined future horizon.
"""
import csv
import io
from research_daily_price_csv_audit import audit_daily_price_csv


def extract_daily_structure(payload, *, mean_window=20, atr_window=14):
    audit_daily_price_csv(payload)
    if type(mean_window) is not int or type(atr_window) is not int or min(mean_window, atr_window) < 2:
        raise ValueError("invalid_window")
    rows = list(csv.DictReader(io.StringIO(payload.decode("utf-8-sig"))))
    bars = [{k: float(row[k]) for k in ("open", "high", "low", "close")}
            | {"date": row["date"]} for row in rows]
    output = []
    tr = []
    for i, bar in enumerate(bars):
        previous_close = bars[i - 1]["close"] if i else bar["close"]
        tr.append(max(bar["high"] - bar["low"],
                      abs(bar["high"] - previous_close),
                      abs(bar["low"] - previous_close)))
        if i + 1 < max(mean_window, atr_window + 1):
            continue
        mean = sum(b["close"] for b in bars[i - mean_window + 1:i + 1]) / mean_window
        current_atr = sum(tr[i - atr_window + 1:i + 1]) / atr_window
        previous_atr = sum(tr[i - atr_window:i]) / atr_window
        output.append({
            "date": bar["date"],
            "structure_above_20d_mean": bar["close"] > mean,
            "atr_expanding": current_atr > previous_atr,
            "atr_value": current_atr,
            "market_20d_positive": None,
            "severe": None,
            "point_in_time_verified": False,
            "trade_ready": False,
        })
    return output
