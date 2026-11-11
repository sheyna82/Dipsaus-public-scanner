"""Fail-closed preflight for publishing real research evidence.

This does NOT grant publishing rights, validate licenses, or upload anything.
The only accepted public artifact category is synthetic fixture data.
"""
from research_source_secret_screen import reject_obvious_secrets


def assess_public_artifact(observation, source_bytes):
    if not isinstance(observation, dict):
        raise ValueError("invalid_observation")
    reject_obvious_secrets(source_bytes)
    if observation.get("synthetic_data_only") is not True:
        return {
            "public_upload_allowed": False,
            "reason": "real_or_unproven_data_publication_requires_separate_review",
            "private_research_possible": True,
            "trade_ready": False,
        }
    if (observation.get("research_only") is not True
            or observation.get("trade_ready") is not False
            or observation.get("future_outcome") is not None
            or observation.get("independent_source_authentication") is not False
            or observation.get("independent_timestamp_proof") is not False):
        raise ValueError("unsafe_synthetic_publication_claims")
    return {
        "public_upload_allowed": True,
        "reason": "explicit_synthetic_fixture_only",
        "private_research_possible": True,
        "trade_ready": False,
    }
