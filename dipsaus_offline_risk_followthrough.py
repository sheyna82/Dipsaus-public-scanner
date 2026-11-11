"""Offline historical follow-through audit; no feeds, orders, or notifications.

Evaluate a risk signal known at session i close using future session closes.
Requires caller-attested split-adjusted OHLC, not independently verified.
"""
import math
from datetime import date


def evaluate_risk_followthrough(rows, signal_index, horizons=(1, 3, 5, 10),
                                metadata=None):
    if (not isinstance(metadata, dict)
            or metadata.get("split_adjusted") is not True
            or metadata.get("ohlc_consistent") is not True
            or not isinstance(metadata.get("source"), str)
            or not metadata["source"].strip()):
        return None
    if (not isinstance(rows, (list, tuple))
            or type(signal_index) is not int
            or signal_index < 0 or signal_index >= len(rows)
            or not isinstance(horizons, (list, tuple))
            or not horizons
            or any(type(h) is not int or h < 1 for h in horizons)):
        return None
    try:
        days = [date.fromisoformat(row["date"]) for row in rows]
        if any(type(row["date"]) is not str or row["date"] != day.isoformat()
               for row, day in zip(rows, days)):
            return None
        if any(b <= a for a, b in zip(days, days[1:])):
            return None
        for row in rows:
            values = [row[k] for k in ("open", "high", "low", "close")]
            if any(type(x) not in (int, float) or not math.isfinite(x) or x <= 0
                   for x in values):
                return None
            if row["low"] > min(row["open"], row["close"]) or row["high"] < max(row["open"], row["close"]):
                return None
    except (KeyError, ValueError, TypeError):
        return None
    baseline = rows[signal_index]["close"]
    outcomes = {}
    for h in horizons:
        idx = signal_index + h
        if idx >= len(rows):
            outcomes[h] = None
            continue
        window = rows[signal_index + 1:idx + 1]
        gaps = [(rows[j]["open"] / rows[j - 1]["close"] - 1) * 100
                for j in range(signal_index + 1, idx + 1)]
        outcomes[h] = {
            "forward_close_return_pct": round((rows[idx]["close"] / baseline - 1) * 100, 4),
            "worst_future_low_pct": round((min(r["low"] for r in window) / baseline - 1) * 100, 4),
            "large_gap_manual_review": any(abs(g) >= 20 for g in gaps),
        }
    return {"signal_close": baseline, "horizons": outcomes,
            "source_attested_not_verified": True, "research_only": True,
            "trade_ready": False, "order_instruction": None}
