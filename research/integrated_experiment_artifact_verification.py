"""Research-only verification of actual experiment input and outcome bytes.

No performance claims. Caller must supply exact source/dataset/outcome bytes
from a reproducible run; paths or names alone are never sufficient.
"""
import hashlib
from integrated_experiment_registry import verify_research_experiment


def verify_experiment_artifacts(bundle, *, dataset_bytes, source_blobs,
                                outcome_bytes=None):
    verify_research_experiment(bundle)
    manifest = bundle["manifest"]
    if type(dataset_bytes) is not bytes or not dataset_bytes:
        raise ValueError("INVALID_EXPERIMENT_DATASET_BYTES")
    if not isinstance(source_blobs, (list, tuple)) or not source_blobs or any(
            type(blob) is not bytes or not blob for blob in source_blobs):
        raise ValueError("INVALID_EXPERIMENT_SOURCE_BYTES")
    if len(source_blobs) != len(manifest["source_sha256"]):
        raise ValueError("EXPERIMENT_SOURCE_COUNT_MISMATCH")
    if hashlib.sha256(dataset_bytes).hexdigest() != manifest["dataset_sha256"]:
        raise ValueError("EXPERIMENT_DATASET_HASH_MISMATCH")
    actual_sources = sorted(hashlib.sha256(blob).hexdigest() for blob in source_blobs)
    if actual_sources != manifest["source_sha256"]:
        raise ValueError("EXPERIMENT_SOURCE_HASH_MISMATCH")
    if manifest["outcome_sha256"] is None:
        if outcome_bytes is not None:
            raise ValueError("UNREGISTERED_EXPERIMENT_OUTCOME")
    elif (type(outcome_bytes) is not bytes or not outcome_bytes
          or hashlib.sha256(outcome_bytes).hexdigest() != manifest["outcome_sha256"]):
        raise ValueError("EXPERIMENT_OUTCOME_HASH_MISMATCH")
    return {
        "schema": "dipsaus_experiment_artifact_verification_v1",
        "experiment_id": manifest["experiment_id"],
        "manifest_sha256": bundle["manifest_sha256"],
        "dataset_bytes_verified": True,
        "source_bytes_verified": len(source_blobs),
        "outcome_bytes_verified": outcome_bytes is not None,
        "historical_source_authenticity_independently_proven": False,
        "out_of_sample_performance_independently_proven": False,
        "trade_ready": False,
    }
