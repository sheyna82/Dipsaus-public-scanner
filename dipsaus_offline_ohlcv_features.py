"""Causal after-close daily OHLCV features; no data fetching or timestamps."""
from datetime import date
import math

def _valid(rows):
    if not isinstance(rows, (list, tuple)) or len(rows) < 22:
        return False
    previous = None
    for row in rows:
        if not isinstance(row, dict):
            return False
        try:
            day = date.fromisoformat(row["date"])
            if day.isoformat() != row["date"] or (previous and day <= previous):
                return False
        except (KeyError, ValueError, TypeError):
            return False
        previous = day
        values = [row.get(k) for k in ("open", "high", "low", "close", "volume")]
        if any(type(v) not in (int, float) or not math.isfinite(v) for v in values):
            return False
        op, hi, lo, close, volume = values
        if min(op, hi, lo, close) <= 0 or volume <= 0 or not lo <= min(op, close) <= max(op, close) <= hi:
            return False
    return True

def calculate_recovery_features(stock, benchmark, days_to_earnings):
    """Calculate six baseline inputs from completed bars through signal close.

    Benchmark and stock require identical dates. Caller must supply real
    as-of timestamps separately; never invent publication times.
    """
    if not _valid(stock) or not _valid(benchmark):
        return None
    if [x["date"] for x in stock] != [x["date"] for x in benchmark]:
        return None
    if type(days_to_earnings) is not int or days_to_earnings < 0:
        return None
    stock_20 = 100 * (stock[-1]["close"] / stock[-21]["close"] - 1)
    benchmark_20 = 100 * (benchmark[-1]["close"] / benchmark[-21]["close"] - 1)
    return_5 = 100 * (stock[-1]["close"] / stock[-6]["close"] - 1)
    market_5 = 100 * (benchmark[-1]["close"] / benchmark[-6]["close"] - 1)
    mean_volume = sum(row["volume"] for row in stock[-21:-1]) / 20
    if mean_volume <= 0:
        return None
    true_ranges = []
    for i in range(len(stock) - 14, len(stock)):
        high, low, prior = stock[i]["high"], stock[i]["low"], stock[i - 1]["close"]
        true_ranges.append(max(high - low, abs(high - prior), abs(low - prior)))
    atr_pct = 100 * (sum(true_ranges) / 14) / stock[-1]["close"]
    result = {"relative_strength_20d": stock_20 - benchmark_20,
              "return_5d": return_5,
              "volume_ratio_20d": stock[-1]["volume"] / mean_volume,
              "atr_pct": atr_pct,
              "market_return_5d": market_5,
              "days_to_earnings": days_to_earnings}
    return result if all(math.isfinite(x) for x in result.values()) else None
