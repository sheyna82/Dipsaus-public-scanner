"""Conservative prospective registration receipt gate.

A GitHub artifact receipt proves publication no earlier than its server-reported
creation time. It does not authenticate the input market data or prove that
registration preceded the market move. No trading permission is granted.
"""
from datetime import datetime, timezone
import re


def _utc(value):
    if not isinstance(value, str):
        raise ValueError("missing_timestamp")
    try:
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("invalid_timestamp") from exc
    if result.tzinfo is None or result.utcoffset() is None:
        raise ValueError("timezone_required")
    return result.astimezone(timezone.utc)


def audit_registration_receipt(candidate, artifact, *, expected_run_id, expected_head_sha):
    if not isinstance(candidate, dict) or not isinstance(artifact, dict):
        raise ValueError("invalid_receipt_input")
    if candidate.get("research_only") is not True or candidate.get("trade_ready") is not False:
        raise ValueError("unsafe_candidate")
    if candidate.get("future_outcome") is not None:
        raise ValueError("future_outcome_present")
    if candidate.get("registration_clock_proof_independent") is not False:
        raise ValueError("unsupported_independent_clock_claim")
    for field in ("protocol_id", "symbol", "signal_session", "candidate_identity_sha256"):
        if not isinstance(candidate.get(field), str) or not candidate[field]:
            raise ValueError("missing_candidate_identity")
    if not re.fullmatch(r"[0-9a-f]{64}", candidate["candidate_identity_sha256"]):
        raise ValueError("invalid_candidate_identity_hash")
    if type(expected_run_id) is not int or expected_run_id <= 0:
        raise ValueError("invalid_expected_run")
    if not isinstance(expected_head_sha, str) or not re.fullmatch(r"[0-9a-f]{40}", expected_head_sha):
        raise ValueError("invalid_expected_head")
    workflow = artifact.get("workflow_run")
    if not isinstance(workflow, dict) or workflow.get("id") != expected_run_id or workflow.get("head_sha") != expected_head_sha:
        raise ValueError("artifact_provenance_mismatch")
    if artifact.get("expired") is not False or type(artifact.get("id")) is not int or artifact["id"] <= 0:
        raise ValueError("artifact_unavailable")
    if not isinstance(artifact.get("digest"), str) or not re.fullmatch(r"sha256:[0-9a-f]{64}", artifact["digest"]):
        raise ValueError("invalid_artifact_digest")
    local_registration = _utc(candidate.get("registered_at_utc"))
    published = _utc(artifact.get("created_at"))
    if published < local_registration:
        raise ValueError("artifact_predates_local_registration")
    # The artifact must actually contain this candidate, verified by its
    # content hash and manifest elsewhere; metadata alone cannot prove it.
    return {
        "status": "receipt_metadata_consistent",
        "candidate_identity_sha256": candidate["candidate_identity_sha256"],
        "github_run_id": expected_run_id,
        "artifact_id": artifact["id"],
        "artifact_created_at_utc": published.isoformat(),
        "local_registration_at_utc_claimed": local_registration.isoformat(),
        "candidate_in_artifact_verified": False,
        "artifact_bytes_verified": False,
        "independent_market_data_provenance": False,
        "independent_pre_signal_timestamp_proof": False,
        "research_only": True,
        "trade_ready": False,
    }
