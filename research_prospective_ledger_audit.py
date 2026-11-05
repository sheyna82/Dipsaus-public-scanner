"""Audit prospective signal/outcome files without mutating either set.

Detects orphan outcomes, modified candidate linkage, and duplicate identities.
Research only. File names are not trusted as identities.
"""
import hashlib
import json
from pathlib import Path


def audit_prospective_ledger(candidate_dir, outcome_dir):
    candidates, outcomes, errors = {}, {}, []
    for path in sorted(Path(candidate_dir).glob("*.json")):
        raw = path.read_bytes()
        record = json.loads(raw)
        identity = (record["protocol_id"], record["symbol"], record["signal_session"])
        if identity in candidates:
            errors.append({"type": "duplicate_candidate_identity", "identity": identity})
        if record.get("future_outcome") is not None or record.get("trade_ready") is not False:
            errors.append({"type": "unsafe_candidate", "identity": identity})
        candidates[identity] = {"sha256": hashlib.sha256(raw).hexdigest(), "path": str(path)}
    for path in sorted(Path(outcome_dir).glob("*.json")):
        record = json.loads(path.read_bytes())
        identity = (record["protocol_id"], record["symbol"], record["signal_session"])
        if identity in outcomes:
            errors.append({"type": "duplicate_outcome_identity", "identity": identity})
        outcomes[identity] = str(path)
        original = candidates.get(identity)
        if original is None:
            errors.append({"type": "orphan_outcome", "identity": identity})
        elif original["sha256"] != record.get("candidate_sha256"):
            errors.append({"type": "candidate_hash_mismatch", "identity": identity})
        if record.get("trade_ready") is not False:
            errors.append({"type": "unsafe_outcome", "identity": identity})
    return {"research_only": True, "trade_ready": False,
            "candidate_count": len(candidates), "outcome_count": len(outcomes),
            "pending_outcome_count": len(set(candidates) - set(outcomes)),
            "integrity_pass": not errors, "errors": errors}
