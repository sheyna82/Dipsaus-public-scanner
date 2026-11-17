"""Offline, deterministic OHLC dataset integrity gate (research only).

A digest proves byte-equivalent canonical content, not the truth or
independence of the data provider. Never grants trade readiness.
"""
import hashlib
import json
import math
from datetime import datetime, timezone


def _timestamp(value):
    if not isinstance(value, str):
        return None
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return dt if dt.tzinfo is not None else None
    except (ValueError, TypeError, OverflowError):
        return None


def canonical_payload(bars):
    return json.dumps(bars, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def attest_ohlcv(bars, *, source, instrument, timeframe, fetched_utc,
                 expected_sha256, now=None, max_age_seconds=900):
    """Fail closed on missing metadata, bad candles, gaps, or digest mismatch."""
    blocked = []
    now = now or datetime.now(timezone.utc)
    if not all(isinstance(x, str) and x.strip() for x in (source, instrument, timeframe, expected_sha256)):
        blocked.append("PROVENANCE_MISSING")
    if timeframe not in ("hourly", "daily"):
        blocked.append("TIMEFRAME_UNSUPPORTED")
    stamp = _timestamp(fetched_utc)
    if stamp is None or now.tzinfo is None or not -30 <= (now-stamp).total_seconds() <= max_age_seconds:
        blocked.append("FETCH_TIME_INVALID_OR_STALE")
    if not isinstance(bars, list) or not 7 <= len(bars) <= 5000:
        blocked.append("BARS_MISSING_OR_INSUFFICIENT")
    else:
        previous = None
        for bar in bars:
            if not isinstance(bar, dict) or not all(k in bar for k in ("time", "open", "high", "low", "close", "volume")):
                blocked.append("BAR_SCHEMA_INVALID")
                break
            ts = _timestamp(bar["time"])
            values = [bar[k] for k in ("open", "high", "low", "close", "volume")]
            if ts is None or (previous is not None and ts <= previous):
                blocked.append("BAR_TIME_NOT_STRICTLY_INCREASING")
                break
            previous = ts
            if any(isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) for v in values):
                blocked.append("BAR_NUMERIC_INVALID")
                break
            o, h, l, c, vol = values
            if not (0 < l <= min(o, c) <= max(o, c) <= h and vol >= 0):
                blocked.append("BAR_OHLC_RANGE_INVALID")
                break
    digest = None
    if not blocked:
        try:
            digest = hashlib.sha256(canonical_payload(bars)).hexdigest()
        except (ValueError, TypeError, OverflowError):
            blocked.append("CANONICAL_ENCODING_FAILED")
        if digest is not None and digest != expected_sha256.lower():
            blocked.append("SHA256_MISMATCH")
    return {"status": "INTEGRITY_MATCH" if not blocked else "UNKNOWN",
            "blocks": sorted(set(blocked)), "sha256": digest if not blocked else None,
            "source": source, "instrument": instrument, "timeframe": timeframe,
            "provider_independently_verified": False, "trade_ready": False}
