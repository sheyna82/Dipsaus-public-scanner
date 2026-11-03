"""Verify GitHub artifact bytes against separately retrieved GitHub API metadata.

This authenticates consistency with GitHub's reported digest, not the market
data, signal timestamp, or provenance of any candidate inside the ZIP.
"""
import hashlib
import re

from research_synthetic_transport_verifier import verify_synthetic_artifact_transport


def verify_github_synthetic_artifact(outer_bytes, artifact_metadata, destination, *,
                                     expected_run_id, expected_head_sha):
    if not isinstance(artifact_metadata, dict):
        raise ValueError("invalid_artifact_metadata")
    if type(expected_run_id) is not int or expected_run_id <= 0:
        raise ValueError("invalid_run_id")
    if not isinstance(expected_head_sha, str) or not re.fullmatch(r"[0-9a-f]{40}", expected_head_sha):
        raise ValueError("invalid_head_sha")
    workflow = artifact_metadata.get("workflow_run")
    if not isinstance(workflow, dict) or workflow.get("id") != expected_run_id or workflow.get("head_sha") != expected_head_sha:
        raise ValueError("github_run_identity_mismatch")
    if artifact_metadata.get("expired") is not False or type(artifact_metadata.get("id")) is not int or artifact_metadata["id"] <= 0:
        raise ValueError("artifact_unavailable")
    claimed = artifact_metadata.get("digest")
    if not isinstance(claimed, str) or not re.fullmatch(r"sha256:[0-9a-f]{64}", claimed):
        raise ValueError("missing_github_digest")
    if not isinstance(outer_bytes, bytes):
        raise ValueError("invalid_outer_bytes")
    actual = hashlib.sha256(outer_bytes).hexdigest()
    if actual != claimed[7:]:
        raise ValueError("github_artifact_digest_mismatch")
    verified = verify_synthetic_artifact_transport(outer_bytes, destination)
    return {
        **verified,
        "status": "github_synthetic_artifact_bytes_verified",
        "github_artifact_id": artifact_metadata["id"],
        "github_run_id": expected_run_id,
        "github_artifact_sha256": actual,
        "external_github_artifact_digest_verified": True,
        "source_authenticated_independently": False,
        "prospective_stock_registration_verified": False,
        "trade_ready": False,
    }
