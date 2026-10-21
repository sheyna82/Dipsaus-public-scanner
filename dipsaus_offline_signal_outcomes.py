"""Pure offline signal-outcome study. No provider, broker, secrets or notifications.

Prices must be chronologically ordered, split-adjusted daily OHLC observations.
A signal is evaluated strictly from the NEXT trading session open; this avoids
assuming fills at a price known only after a signal was observed.
"""
import math
from datetime import date


def _price(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value) and value > 0


def evaluate_signal(prices, signal_index, horizons=(1, 3, 5, 10)):
    """Evaluate forward returns and excursion using supplied OHLC rows.

    Returns None for invalid inputs. Incomplete horizons remain None, never
    silently converted to zero or truncated.
    """
    if not isinstance(prices, (list, tuple)) or not isinstance(signal_index, int) or isinstance(signal_index, bool):
        return None
    if signal_index < 0 or signal_index + 1 >= len(prices):
        return None
    if not horizons or any(not isinstance(h, int) or isinstance(h, bool) or h < 1 for h in horizons):
        return None
    if any(not isinstance(row, dict) or any(not _price(row.get(k)) for k in ("open", "high", "low", "close")) or row["low"] > min(row["open"], row["close"]) or row["high"] < max(row["open"], row["close"]) for row in prices):
        return None
    # Require ISO dates in strictly increasing session order.
    try:
        dates = [date.fromisoformat(row["date"]) for row in prices]
    except (KeyError, ValueError, TypeError):
        return None
    if any(not isinstance(row["date"], str) or row["date"] != d.isoformat()
           for row, d in zip(prices, dates)):
        return None
    if any(later <= earlier for earlier, later in zip(dates, dates[1:])):
        return None
    entry = prices[signal_index + 1]["open"]
    result = {"entry_open": entry, "horizons": {}}
    for horizon in horizons:
        end = signal_index + horizon
        if end >= len(prices):
            result["horizons"][horizon] = None
            continue
        # Includes the next session through the horizon-th future session.
        window = prices[signal_index + 1:end + 1]
        result["horizons"][horizon] = {
            "close_return_pct": round((window[-1]["close"] / entry - 1) * 100, 4),
            "max_favorable_pct": round((max(r["high"] for r in window) / entry - 1) * 100, 4),
            "max_adverse_pct": round((min(r["low"] for r in window) / entry - 1) * 100, 4),
        }
    return result
