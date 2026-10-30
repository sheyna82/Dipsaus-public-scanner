"""Fail-closed evidence gate for independent ATR holdout scoring.

This verifies supplied metadata consistency, NOT external provider truth.
No raw data, secrets, positions or network calls are used.
"""
from datetime import date, datetime
from dipsaus_offline_dataset_manifest import validate_dataset_manifest


def assess_holdout_readiness(manifest, audit):
    errors = []
    manifest_result = validate_dataset_manifest(manifest)
    if not manifest_result["accepted"]:
        errors.extend("manifest_" + item for item in manifest_result["errors"])
    if not isinstance(audit, dict):
        audit = {}
    for field in ("provider_rights_checked", "raw_data_sha256_checked",
                  "corporate_actions_independently_verified",
                  "delisted_coverage_verified", "security_identity_asof_verified",
                  "benchmark_sessions_verified", "signal_timestamps_verified",
                  "outcomes_uninspected_before_freeze"):
        if audit.get(field) is not True:
            errors.append("missing_" + field)
    freeze = audit.get("protocol_frozen_at")
    first = audit.get("first_holdout_signal_at")
    try:
        if not isinstance(freeze, str) or not isinstance(first, str):
            raise ValueError("missing")
        frozen_at = datetime.fromisoformat(freeze)
        first_at = datetime.fromisoformat(first)
        if (frozen_at.tzinfo is None or first_at.tzinfo is None
                or not frozen_at < first_at):
            errors.append("invalid_freeze_order")
    except (ValueError, TypeError):
        errors.append("invalid_freeze_timestamps")
    if audit.get("independent_signal_days", 0) < 100:
        errors.append("insufficient_signal_days")
    if audit.get("independent_severe_events", 0) < 30:
        errors.append("insufficient_severe_events")
    return {"status": "DATA_BLOCKED" if errors else "METADATA_REVIEW_REQUIRED",
            "errors": sorted(set(errors)), "metadata_attested": not errors,
            "independent_holdout_verified": False, "trade_ready": False,
            "note": "Caller attestations never establish independent source verification."}
