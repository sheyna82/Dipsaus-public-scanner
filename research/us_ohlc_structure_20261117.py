"""Deterministic OHLC swing-level extraction for offline US research.

No external requests. This is evidence generation, not independent provider
attestation or broker execution clearance.
"""
import math
from datetime import datetime, timezone


def _valid_bar(bar):
    if not isinstance(bar, dict):
        return False
    try:
        low, high, close = (bar[k] for k in ("low", "high", "close"))
        if any(isinstance(x, bool) or not isinstance(x, (int, float)) or not math.isfinite(x) for x in (low, high, close)):
            return False
        return 0 < low <= close <= high
    except KeyError:
        return False


def swing_evidence(bars, dataset_id, source, timeframe, checked_utc, window=2, now=None):
    """Return confirmed local extrema excluding the last 'window' bars.

    Every pivot must exceed neighboring highs / undercut neighboring lows.
    Returns levels without a verified flag: external source admission remains
    a separate gate.
    """
    now = now or datetime.now(timezone.utc)
    if not isinstance(dataset_id, str) or not dataset_id.strip() or not isinstance(source, str) or not source.strip():
        return {"status": "UNKNOWN", "reason": "SOURCE_MISSING"}
    if timeframe not in ("hourly", "daily") or not isinstance(window, int) or isinstance(window, bool) or not 1 <= window <= 10:
        return {"status": "UNKNOWN", "reason": "PARAMETERS_INVALID"}
    try:
        stamp = datetime.fromisoformat(checked_utc.replace("Z", "+00:00"))
        age = (now - stamp).total_seconds()
        if stamp.tzinfo is None or not -30 <= age <= 900:
            return {"status": "UNKNOWN", "reason": "STALE_DATASET"}
    except (ValueError, TypeError, AttributeError, OverflowError):
        return {"status": "UNKNOWN", "reason": "TIMESTAMP_INVALID"}
    if not isinstance(bars, list) or len(bars) < 2 * window + 3 or len(bars) > 5000 or not all(_valid_bar(x) for x in bars):
        return {"status": "UNKNOWN", "reason": "OHLC_INVALID_OR_INSUFFICIENT"}
    highs, lows = [], []
    for i in range(window, len(bars) - window):
        h, l = bars[i]["high"], bars[i]["low"]
        neighbors = bars[i-window:i] + bars[i+1:i+window+1]
        if all(h > b["high"] for b in neighbors):
            highs.append((i, h))
        if all(l < b["low"] for b in neighbors):
            lows.append((i, l))
    return {"status": "STRUCTURE_FOUND" if highs and lows else "STRUCTURE_INCOMPLETE",
            "swing_highs": highs, "swing_lows": lows,
            "dataset_id": dataset_id, "source": source, "timeframe": timeframe,
            "checked_utc": checked_utc, "method": "strict_local_pivot",
            "verified": False, "trade_ready": False}
