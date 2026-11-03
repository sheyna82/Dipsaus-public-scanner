"""Research-only local immutable candidate registration.

The local clock is not an independently trusted timestamp authority.
A subsequent external artifact receipt is required for independent evidence.
"""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


def register_candidate_once(candidate, directory, *, clock=None):
    if not isinstance(candidate, dict) or candidate.get("trade_ready") is not False:
        raise ValueError("unsafe_candidate")
    if candidate.get("future_outcome") is not None:
        raise ValueError("candidate_contains_future_outcome")
    if "registered_at_utc" in candidate:
        raise ValueError("caller_supplied_registration_time_forbidden")
    for key in ("symbol", "signal_session", "protocol_id"):
        if not isinstance(candidate.get(key), str) or not candidate[key]:
            raise ValueError("missing_candidate_identity")
    now = clock() if clock is not None else datetime.now(timezone.utc)
    if not isinstance(now, datetime) or now.tzinfo is None or now.utcoffset() is None:
        raise ValueError("utc_clock_required")
    if now.utcoffset().total_seconds() != 0:
        raise ValueError("utc_clock_required")
    timestamp = now.astimezone(timezone.utc).isoformat()
    record = dict(candidate)
    record["registered_at_utc"] = timestamp
    record["registration_clock_proof_independent"] = False
    record["research_only"] = True
    record["trade_ready"] = False
    payload = (json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
    root = Path(directory)
    if not root.is_dir():
        raise ValueError("candidate_directory_must_exist")
    # Use content-derived identity; the write is exclusive and cannot overwrite.
    digest = hashlib.sha256(payload).hexdigest()
    path = root / (digest + ".json")
    try:
        with path.open("xb") as out:
            out.write(payload)
    except FileExistsError:
        if path.read_bytes() != payload:
            raise ValueError("candidate_hash_collision_or_conflict")
        return {"status": "duplicate", "path": str(path), "sha256": digest,
                "independent_timestamp_proof": False, "trade_ready": False}
    return {"status": "created", "path": str(path), "sha256": digest,
            "registered_at_utc": timestamp, "independent_timestamp_proof": False,
            "trade_ready": False}
