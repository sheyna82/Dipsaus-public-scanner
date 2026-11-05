"""Research dataset manifest validation. Metadata is caller-attested, not verified.

A valid manifest is necessary but insufficient for claiming historical performance.
No network requests or proprietary data are embedded.
"""
from datetime import datetime, timezone
from urllib.parse import urlparse

REQUIRED = ("provider", "source_url", "license_name", "license_url",
            "retrieved_at", "price_adjustment", "timezone",
            "survivorship_policy", "corporate_actions_policy",
            "point_in_time_policy", "universe_definition")


def validate_dataset_manifest(manifest):
    if not isinstance(manifest, dict):
        return {"accepted": False, "errors": ["invalid_manifest"], "source_verified": False}
    errors = []
    for field in REQUIRED:
        if not isinstance(manifest.get(field), str) or not manifest[field].strip():
            errors.append("missing_" + field)
    for field in ("source_url", "license_url"):
        value = manifest.get(field)
        if isinstance(value, str):
            parsed = urlparse(value)
            if parsed.scheme != "https" or not parsed.netloc or parsed.username or parsed.password:
                errors.append("invalid_" + field)
    timestamp = manifest.get("retrieved_at")
    if isinstance(timestamp, str):
        try:
            dt = datetime.fromisoformat(timestamp)
            if dt.tzinfo is None or dt.utcoffset() is None:
                errors.append("naive_retrieval_timestamp")
            elif dt.astimezone(timezone.utc) > datetime.now(timezone.utc):
                errors.append("future_retrieval_timestamp")
        except ValueError:
            errors.append("invalid_retrieval_timestamp")
    if manifest.get("price_adjustment") not in ("split_adjusted", "raw"):
        errors.append("unsupported_price_adjustment")
    if manifest.get("point_in_time_policy") != "verified_release_timestamps":
        errors.append("point_in_time_unverified")
    if manifest.get("survivorship_policy") == "survivors_only":
        errors.append("survivorship_bias_unaddressed")
    return {"accepted": not errors, "errors": sorted(set(errors)),
            "source_verified": False, "trade_ready": False,
            "warning": "Manifest declarations are not independent evidence of license, completeness or data quality."}
