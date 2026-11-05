"""Bind a local candidate record to an already verified downloaded archive.

Archive verification and GitHub receipt verification are separate prerequisites.
This function never elevates research evidence into trading authorization.
"""
import hashlib
import json


def bind_candidate_to_archive(candidate, archive_summary, receipt_summary):
    if not isinstance(candidate, dict) or not isinstance(archive_summary, dict) or not isinstance(receipt_summary, dict):
        raise ValueError("invalid_binding_input")
    if archive_summary.get("status") != "archive_manifest_verified":
        raise ValueError("archive_not_verified")
    if receipt_summary.get("status") != "receipt_metadata_consistent":
        raise ValueError("receipt_not_verified")
    if candidate.get("trade_ready") is not False or candidate.get("research_only") is not True:
        raise ValueError("unsafe_candidate")
    identity = candidate.get("candidate_identity_sha256")
    if not isinstance(identity, str) or receipt_summary.get("candidate_identity_sha256") != identity:
        raise ValueError("receipt_candidate_mismatch")
    payload = (json.dumps(candidate, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
    digest = hashlib.sha256(payload).hexdigest()
    entries = archive_summary.get("candidates")
    if not isinstance(entries, list):
        raise ValueError("invalid_archive_summary")
    matching = [entry for entry in entries if isinstance(entry, dict) and entry.get("identity") == identity]
    if len(matching) != 1 or matching[0].get("sha256") != digest:
        raise ValueError("candidate_not_uniquely_bound_to_archive")
    return {
        "status": "candidate_archive_content_bound",
        "candidate_identity_sha256": identity,
        "candidate_payload_sha256": digest,
        "github_run_id": receipt_summary["github_run_id"],
        "artifact_id": receipt_summary["artifact_id"],
        "candidate_in_artifact_verified": True,
        "github_artifact_download_digest_verified": False,
        "independent_market_data_provenance": False,
        "independent_pre_signal_timestamp_proof": False,
        "research_only": True,
        "trade_ready": False,
    }
