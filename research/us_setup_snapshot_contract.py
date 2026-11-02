"""Research-only immutable episode-evaluation snapshot contract.

Canonical hashes detect accidental data changes between evaluation runs. A hash
does not establish market data quality, independence of human labels, or OOS.
"""
import hashlib
import json
from datetime import datetime, timezone


def _time(value):
    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        raise ValueError("TIMESTAMP_MUST_HAVE_TIMEZONE")
    return dt.astimezone(timezone.utc)


def freeze_snapshot(symbol, bars, reference_episodes, *, label_provenance, split):
    if split not in ("train", "validation", "test"):
        raise ValueError("UNDECLARED_SPLIT")
    if not isinstance(label_provenance, dict):
        raise ValueError("LABEL_PROVENANCE_REQUIRED")
    for key in ("annotator", "method", "labeled_at_utc", "source_dataset"):
        if not isinstance(label_provenance.get(key), str) or not label_provenance[key].strip():
            raise ValueError("INCOMPLETE_LABEL_PROVENANCE")
    _time(label_provenance["labeled_at_utc"])
    if not symbol or not isinstance(symbol, str):
        raise ValueError("INVALID_SYMBOL")
    previous = None
    for bar in bars:
        ts = _time(bar["timestamp"])
        if previous is not None and ts <= previous:
            raise ValueError("UNSORTED_BARS")
        previous = ts
    for label in reference_episodes:
        _time(label["confirmed_utc"])
        if not label.get("source"):
            raise ValueError("UNSOURCED_LABEL")
    payload = {"schema_version": 1, "symbol": symbol, "split": split,
               "bars": bars, "reference_episodes": reference_episodes,
               "label_provenance": label_provenance}
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    return {"snapshot": payload, "sha256": hashlib.sha256(encoded).hexdigest(),
            "independence_verified": False, "research_only": True}


def verify_snapshot(frozen):
    payload = frozen["snapshot"]
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    return hashlib.sha256(encoded).hexdigest() == frozen["sha256"]
