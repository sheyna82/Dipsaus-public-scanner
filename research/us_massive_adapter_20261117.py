"""Offline Massive aggregate-bars adapter. No network, trust attestation or trade signals."""
from datetime import datetime, timezone
import math

def normalize_massive_aggregates(payload, *, ticker, mic, adjustment_policy):
    blocks = []
    if not isinstance(payload, dict) or not isinstance(payload.get("results"), list):
        blocks.append("RESULTS_MISSING")
    if not isinstance(ticker, str) or not ticker.strip() or not isinstance(mic, str) or len(mic) != 4:
        blocks.append("INSTRUMENT_METADATA_INVALID")
    if adjustment_policy not in ("split_adjusted", "unadjusted"):
        blocks.append("ADJUSTMENT_POLICY_UNKNOWN")
    if isinstance(payload, dict) and payload.get("ticker") != ticker:
        blocks.append("TICKER_MISMATCH")
    # The requested adjustment mode must agree with the response metadata
    # when supplied. Missing metadata remains unknown, not silently trusted.
    if isinstance(payload, dict):
        adjusted = payload.get("adjusted")
        if type(adjusted) is not bool:
            blocks.append("ADJUSTMENT_METADATA_MISSING")
        elif adjustment_policy in ("split_adjusted", "unadjusted") and adjusted != (adjustment_policy == "split_adjusted"):
            blocks.append("ADJUSTMENT_MISMATCH")
    bars = []
    if not blocks:
        previous = None
        for raw in payload["results"]:
            if not isinstance(raw, dict) or any(k not in raw for k in ("t", "o", "h", "l", "c", "v")):
                blocks.append("BAR_SCHEMA_INVALID")
                break
            t = raw["t"]
            vals = [raw[k] for k in ("o", "h", "l", "c", "v")]
            if isinstance(t, bool) or not isinstance(t, int) or t < 0 or (previous is not None and t <= previous):
                blocks.append("TIMESTAMP_INVALID_OR_UNSORTED")
                break
            if any(isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) for v in vals):
                blocks.append("BAR_NUMERIC_INVALID")
                break
            o, h, l, c, v = vals
            if not (0 < l <= min(o, c) <= max(o, c) <= h and v >= 0):
                blocks.append("BAR_OHLC_INVALID")
                break
            try:
                stamp = datetime.fromtimestamp(t / 1000, tz=timezone.utc).isoformat().replace("+00:00", "Z")
            except (OverflowError, OSError, ValueError):
                blocks.append("TIMESTAMP_INVALID_OR_UNSORTED")
                break
            bars.append({"time": stamp, "open": o, "high": h, "low": l, "close": c, "volume": v})
            previous = t
    if not bars:
        blocks.append("NO_VALID_BARS")
    return {"status": "NORMALIZED_UNVERIFIED" if not blocks else "UNKNOWN",
            "blocks": sorted(set(blocks)), "bars": bars if not blocks else [],
            "provider_id": "massive", "instrument_id": ticker, "mic": mic,
            "adjustment_policy": adjustment_policy,
            "provider_independently_verified": False, "trade_ready": False}
