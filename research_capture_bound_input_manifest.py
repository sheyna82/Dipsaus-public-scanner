"""Research-only capture-bound input audit; not a prospective signal claim."""
import hashlib
import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
from research_yahoo_probe_evidence_audit import audit_yahoo_probe


def audit_capture_bound_inputs(root, symbols=("COHU", "AMD", "META", "SPY")):
    root = Path(root)
    if len(set(symbols)) != len(symbols) or "SPY" not in symbols:
        raise ValueError("invalid_capture_symbol_set")
    evidence = [audit_yahoo_probe(root, symbol) for symbol in symbols]
    if not all(row["accepted"] for row in evidence):
        raise ValueError("incomplete_capture_evidence")
    # The source receipt timestamps are not independently authenticated.
    # Never backdate a candidate to a historical signal session.
    timestamps = [datetime.fromisoformat(row["retrieved_at_utc"]) for row in evidence]
    captured_at = max(timestamps).isoformat()
    last_common_session = min(row["last_conservatively_eligible_session"] for row in evidence)
    manifest = {
        "research_only": True, "trade_ready": False,
        "captured_at_utc": captured_at,
        "last_common_eligible_session": last_common_session,
        "sources": {row["symbol"]: {
            "raw_sha256": row["raw_sha256"],
            "retrieved_at_utc": row["retrieved_at_utc"],
            "last_eligible_session": row["last_conservatively_eligible_session"]}
            for row in evidence},
        "independent_prospective_proof": False,
        "prospective_candidate_registered": False,
        "outcome_window_must_start_after_capture": True,
    }
    return manifest


def write_capture_manifest(root, output):
    output = Path(output)
    if output.exists():
        raise ValueError("capture_manifest_already_exists")
    manifest = audit_capture_bound_inputs(root)
    payload = (json.dumps(manifest, sort_keys=True, indent=2) + "\n").encode()
    with output.open("xb") as stream:
        stream.write(payload)
    return {"path": str(output), "sha256": hashlib.sha256(payload).hexdigest(),
            "prospective_candidate_registered": False}
