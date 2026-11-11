"""Fail-closed reconciliation of GitHub artifact metadata and synthetic claims.

GitHub API metadata is trusted only as an API observation, not independent
authentication of market data or of the checkout commit inside an artifact.
"""
import re

_SHA = re.compile(r"^[0-9a-f]{64}$")


def reconcile_synthetic_artifact(record, artifact, *, expected_run_id, expected_head_sha):
    """Compare claims against separately retrieved GitHub run/artifact metadata.

    expected_head_sha must come from the GitHub PR/run head, not GITHUB_SHA:
    pull_request workflows can check out an ephemeral merge commit.
    """
    if not isinstance(record, dict) or not isinstance(artifact, dict):
        raise ValueError("invalid_metadata")
    if record.get("synthetic_data_only") is not True or record.get("research_only") is not True:
        raise ValueError("not_synthetic_research")
    if record.get("trade_ready") is not False or record.get("future_outcome") is not None:
        raise ValueError("unsafe_research_status")
    if type(expected_run_id) is not int or expected_run_id <= 0:
        raise ValueError("invalid_expected_run")
    if not isinstance(expected_head_sha, str) or not re.fullmatch("[0-9a-f]{40}", expected_head_sha):
        raise ValueError("invalid_expected_head")
    if record.get("github_run_id_claimed") != str(expected_run_id):
        raise ValueError("run_claim_mismatch")
    if artifact.get("id") is None or type(artifact["id"]) is not int or artifact["id"] <= 0:
        raise ValueError("invalid_artifact_id")
    if artifact.get("expired") is not False:
        raise ValueError("artifact_expired_or_unknown")
    workflow = artifact.get("workflow_run")
    if not isinstance(workflow, dict) or workflow.get("id") != expected_run_id:
        raise ValueError("artifact_run_mismatch")
    if workflow.get("head_sha") != expected_head_sha:
        raise ValueError("artifact_head_mismatch")
    digest = artifact.get("digest")
    if not isinstance(digest, str) or not digest.startswith("sha256:") or not _SHA.fullmatch(digest[7:]):
        raise ValueError("invalid_artifact_digest")
    checkout = record.get("workflow_checkout_sha_claimed", record.get("head_sha_claimed"))
    if not isinstance(checkout, str) or not re.fullmatch("[0-9a-f]{40}", checkout):
        raise ValueError("invalid_checkout_claim")
    return {
        "status": "github_metadata_reconciled",
        "run_id": expected_run_id,
        "artifact_id": artifact["id"],
        "artifact_digest": digest,
        "pr_head_sha": expected_head_sha,
        "workflow_checkout_sha_claimed": checkout,
        "workflow_checkout_authenticated": False,
        "download_digest_verified": False,
        "source_authenticated_independently": False,
        "registered_stock_candidates": 0,
        "trade_ready": False,
    }
