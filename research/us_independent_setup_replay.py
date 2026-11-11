"""Research-only independent recovery setup lifecycle; no notification promotion.

A reset is evidenced by an observed break below the prior setup's low followed
by a later, distinct confirmed rebound. This intentionally conservative proxy
does not establish a money-qualified entry or production-ready setup identity.
"""
from dataclasses import dataclass
from datetime import datetime
import hashlib
import json
import math


@dataclass(frozen=True)
class Bar:
    timestamp: str
    low: float
    close: float


def _parse(bars):
    result = []
    last = None
    for row in bars:
        ts = datetime.fromisoformat(row["timestamp"].replace("Z", "+00:00"))
        if ts.tzinfo is None or (last is not None and ts <= last):
            raise ValueError("NON_MONOTONIC_OR_NAIVE_TIMESTAMP")
        low, close = float(row["low"]), float(row["close"])
        if not (math.isfinite(low) and math.isfinite(close) and 0 < low <= close):
            raise ValueError("INVALID_BAR")
        result.append((ts, low, close))
        last = ts
    return result


def replay(symbol, bars, *, rebound_pct=1.0, reset_pct=1.0, confirmation_bars=3):
    """Prefix-only detector. No live alerts; candidates remain unverified.

    A new episode is counted only after a lower low at least reset_pct below
    the prior confirmed episode low and confirmation_bars later rising closes.
    """
    if not isinstance(symbol, str) or not symbol or not symbol.replace(".", "").isalnum():
        raise ValueError("INVALID_SYMBOL")
    if not (0 < rebound_pct <= 50 and 0 < reset_pct <= 50 and 2 <= confirmation_bars <= 20):
        raise ValueError("INVALID_PARAMETERS")
    seq = _parse(bars)
    events = []
    candidate_low = None
    candidate_index = None
    active_low = None
    reset_required = False
    for i, (ts, low, close) in enumerate(seq):
        if active_low is not None and not reset_required:
            if low <= active_low * (1 - reset_pct / 100):
                reset_required = True
                candidate_low, candidate_index = low, i
            else:
                continue
        elif candidate_low is None or low < candidate_low:
            candidate_low, candidate_index = low, i
        if candidate_index is None or i - candidate_index < confirmation_bars:
            continue
        window = seq[i - confirmation_bars + 1:i + 1]
        rising = all(window[j][2] > window[j - 1][2] for j in range(1, len(window)))
        if rising and close >= candidate_low * (1 + rebound_pct / 100):
            anchor = seq[candidate_index][0].isoformat()
            digest = hashlib.sha256(json.dumps([symbol, anchor, round(candidate_low, 6)]).encode()).hexdigest()[:16]
            events.append({"symbol": symbol, "candidate_setup_id": "R-" + digest,
                           "anchor_utc": anchor, "confirmed_utc": ts.isoformat(),
                           "anchor_low": candidate_low,
                           "independent_setup_verified": False,
                           "notification_eligible": False,
                           "research_only": True})
            active_low = candidate_low
            reset_required = False
            candidate_low, candidate_index = None, None
    return events
