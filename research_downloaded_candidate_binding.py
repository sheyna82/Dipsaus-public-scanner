"""Offline, fail-closed binding of downloaded GitHub artifact bytes to a candidate.

The GitHub metadata and expected identifiers must be obtained independently by
the caller. This function does not authenticate the provider or signal timing.
"""
import hashlib
import io
from zipfile import ZipFile

from research_real_candidate_artifact_verifier import verify_real_candidate_artifact
from research_registration_archive_bridge import inspect_candidate_archive
from research_registration_receipt_gate import audit_registration_receipt
from research_candidate_artifact_content_binding import bind_candidate_to_archive


def verify_downloaded_candidate_binding(outer_bytes, metadata, candidate, *,
                                        expected_run_id, expected_head_sha,
                                        expected_archive_sha256, max_bytes=8_000_000):
    if not isinstance(candidate, dict):
        raise ValueError("invalid_candidate")
    identity = candidate.get("candidate_identity_sha256")
    transport = verify_real_candidate_artifact(
        outer_bytes, metadata, expected_run_id=expected_run_id,
        expected_head_sha=expected_head_sha,
        expected_archive_sha256=expected_archive_sha256,
        expected_candidate_identity_sha256=identity, max_bytes=max_bytes)
    # No caller-supplied archive summary is trusted. Derive it from the exact
    # downloaded bytes already checked against GitHub's reported digest.
    with ZipFile(io.BytesIO(outer_bytes)) as outer:
        with outer.open("candidate-archive.zip") as handle:
            inner = handle.read(max_bytes + 1)
    if len(inner) > max_bytes or hashlib.sha256(inner).hexdigest() != expected_archive_sha256:
        raise ValueError("archive_bytes_changed")
    with ZipFile(io.BytesIO(inner)) as archive:
        entries = archive.infolist()
        if len(entries) > 256 or sum(x.file_size for x in entries) > max_bytes:
            raise ValueError("archive_expansion_limit")
        if any(x.is_dir() or x.file_size > max_bytes for x in entries):
            raise ValueError("invalid_inner_member")
    archive_summary = inspect_candidate_archive(io.BytesIO(inner))
    receipt = audit_registration_receipt(
        candidate, metadata, expected_run_id=expected_run_id,
        expected_head_sha=expected_head_sha)
    bound = bind_candidate_to_archive(candidate, archive_summary, receipt)
    if bound["candidate_identity_sha256"] != transport["candidate_identity_sha256"]:
        raise ValueError("transport_candidate_mismatch")
    return {
        "status": "downloaded_artifact_candidate_content_bound",
        "github_run_id": expected_run_id,
        "github_artifact_id": metadata["id"],
        "candidate_identity_sha256": identity,
        "github_artifact_download_digest_verified": True,
        "candidate_in_downloaded_artifact_verified": True,
        "receipt_timing_classification": receipt["receipt_timing_classification"],
        "independent_market_data_provenance": False,
        "independent_pre_signal_timestamp_proof": False,
        "prospective_signal_proven": False,
        "research_only": True,
        "trade_ready": False,
    }
