"""Research-only reconciliation of independently collected immutable candidate files.

The caller must supply the complete known collection. This does not fetch artifacts,
prove completeness, authenticate external timestamps, or update a live scanner.
"""
import hashlib
import json
from pathlib import Path


def reconcile_candidate_records(paths):
    records = {}
    seen_files = set()
    for item in paths:
        path = Path(item)
        raw = path.read_bytes()
        digest = hashlib.sha256(raw).hexdigest()
        if digest in seen_files:
            continue
        seen_files.add(digest)
        record = json.loads(raw)
        if not isinstance(record, dict) or record.get("trade_ready") is not False:
            raise ValueError("unsafe_candidate")
        if record.get("future_outcome") is not None:
            raise ValueError("candidate_contains_future_outcome")
        identity = {key: record[key] for key in ("protocol_id", "symbol", "signal_session")}
        identity_digest = hashlib.sha256(
            json.dumps(identity, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()
        if record.get("candidate_identity_sha256") != identity_digest:
            raise ValueError("candidate_identity_digest_mismatch")
        if not record.get("registered_at_utc"):
            raise ValueError("missing_registration_timestamp")
        previous = records.get(identity_digest)
        if previous is not None and previous["sha256"] != digest:
            raise ValueError("cross_run_candidate_registration_conflict")
        records[identity_digest] = {
            "identity_sha256": identity_digest,
            "sha256": digest,
            "registered_at_utc": record["registered_at_utc"],
            "protocol_id": record["protocol_id"],
            "symbol": record["symbol"],
            "signal_session": record["signal_session"],
        }
    return {
        "status": "reconciled_known_inputs_only",
        "candidate_count": len(records),
        "candidates": sorted(records.values(), key=lambda r: r["identity_sha256"]),
        "collection_complete_independently": False,
        "timestamps_authenticated_independently": False,
        "research_only": True,
        "trade_ready": False,
    }
