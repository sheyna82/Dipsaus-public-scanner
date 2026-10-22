"""Check that frozen signals are invariant to all future OHLCV values.

Offline causal lookahead audit. It tests the frozen signal predicate, NOT
corporate-action or point-in-time fundamentals provenance.
"""
from copy import deepcopy
from dipsaus_offline_ohlcv_features import _valid


def frozen_signal_at(rows, i):
    if not _valid(rows) or type(i) is not int or i < 21 or i >= len(rows):
        return {"status": "DATA_BLOCKED", "reason": "invalid_history_or_index"}
    last = rows[i]
    trend = (rows[i - 2]["close"] < rows[i - 1]["close"] < last["close"]
             and last["close"] > sum(x["close"] for x in rows[i - 5:i]) / 5)
    prior = rows[i - 1]["close"]
    mean_range = sum(x["high"] - x["low"] for x in rows[i - 14:i]) / 14
    risk = (last["close"] / prior - 1 <= -0.03 or
            last["high"] - last["low"] > 2 * mean_range)
    return {"status": "CAUSAL_SIGNAL_CHECK", "signal": bool(trend and not risk)}


def audit_future_invariance(rows, *, indices=None):
    if not _valid(rows) or len(rows) < 25:
        return {"status": "DATA_BLOCKED", "reason": "invalid_history"}
    if indices is None:
        indices = list(range(21, len(rows) - 1))
    if not isinstance(indices, (list, tuple)) or not indices:
        return {"status": "DATA_BLOCKED", "reason": "invalid_indices"}
    checked = 0
    for i in indices:
        if type(i) is not int or i < 21 or i >= len(rows) - 1:
            return {"status": "DATA_BLOCKED", "reason": "invalid_index"}
        original = frozen_signal_at(rows[:i + 1], i)
        if original["status"] != "CAUSAL_SIGNAL_CHECK":
            return {"status": "DATA_BLOCKED", "reason": "invalid_original"}
        changed = deepcopy(rows[:i + 1])
        # Append future bars with radically different, but internally valid,
        # prices. The past through the signal close is untouched.
        for k, future in enumerate(rows[i + 1:]):
            bar = dict(future)
            scale = 1.7 if k % 2 == 0 else 0.4
            for key in ("open", "high", "low", "close"):
                bar[key] = future[key] * scale
            changed.append(bar)
        if not _valid(changed):
            return {"status": "DATA_BLOCKED", "reason": "mutated_history_invalid"}
        after = frozen_signal_at(changed, i)
        if after != original:
            return {"status": "LOOKAHEAD_DETECTED", "index": i, "trade_ready": False}
        checked += 1
    return {"status": "EXPLORATORY_CAUSAL_INVARIANCE", "checked_signals": checked,
            "lookahead_detected": False, "corporate_actions_verified": False,
            "earnings_asof_verified": False, "trade_ready": False}
