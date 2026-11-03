"""Bind a frozen market-source response to its bytes, without authenticating it.

This is a research-only local evidence envelope. The response must be captured
separately; a URL or a SHA-256 hash alone is not proof of market authenticity.
"""
import hashlib
import re


def bind_source_snapshot(observation, source_bytes, *, expected_sha256):
    if not isinstance(observation, dict):
        raise ValueError("invalid_observation")
    if not isinstance(source_bytes, bytes) or not source_bytes:
        raise ValueError("missing_source_bytes")
    if len(source_bytes) > 5_000_000:
        raise ValueError("source_snapshot_too_large")
    if not isinstance(expected_sha256, str) or not re.fullmatch(r"[0-9a-f]{64}", expected_sha256):
        raise ValueError("invalid_expected_sha256")
    digest = hashlib.sha256(source_bytes).hexdigest()
    if digest != expected_sha256:
        raise ValueError("source_snapshot_digest_mismatch")
    if observation.get("independent_source_authentication") is not False:
        raise ValueError("unsupported_source_authentication_claim")
    if observation.get("independent_timestamp_proof") is not False:
        raise ValueError("unsupported_timestamp_claim")
    if observation.get("trade_ready") is not False or observation.get("research_only") is not True:
        raise ValueError("unsafe_observation")
    if observation.get("future_outcome") is not None:
        raise ValueError("future_outcome_forbidden")
    if "source_snapshot_sha256" in observation or "source_snapshot_bytes" in observation:
        raise ValueError("caller_supplied_source_snapshot_metadata_forbidden")
    record = dict(observation)
    record["source_snapshot_sha256"] = digest
    record["source_snapshot_bytes"] = len(source_bytes)
    record["source_snapshot_verified_locally"] = True
    record["independent_source_authentication"] = False
    record["independent_timestamp_proof"] = False
    record["trade_ready"] = False
    return record
