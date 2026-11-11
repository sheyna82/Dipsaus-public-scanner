"""Offline research dataset manifest: no fake samples, no network fetching.

Price/event source metadata and survivorship coverage are mandatory before
historical profit comparisons. A manifest is not proof of license or quality.
"""
from research_swing_event_dataset_audit import _utc

REQUIRED = ("dataset_id", "market", "source_url", "retrieved_at",
            "as_of_at", "price_adjustment", "currency",
            "includes_delisted", "license_reviewed", "event_timestamp_policy")
ADJUSTMENTS = ("raw", "split_adjusted", "total_return")


def validate_research_dataset_manifest(manifest):
    if not isinstance(manifest, dict):
        raise ValueError("invalid_manifest")
    for key in REQUIRED:
        if key not in manifest:
            raise ValueError("missing_" + key)
    for key in ("dataset_id", "market", "currency", "event_timestamp_policy"):
        if not isinstance(manifest[key], str) or not manifest[key].strip():
            raise ValueError("invalid_" + key)
    if not isinstance(manifest["source_url"], str) or not manifest["source_url"].startswith("https://"):
        raise ValueError("invalid_source_url")
    if manifest["price_adjustment"] not in ADJUSTMENTS:
        raise ValueError("unknown_adjustment")
    if type(manifest["includes_delisted"]) is not bool:
        raise ValueError("unknown_survivorship_coverage")
    if type(manifest["license_reviewed"]) is not bool:
        raise ValueError("unknown_license_status")
    retrieved, asof = _utc(manifest["retrieved_at"]), _utc(manifest["as_of_at"])
    if asof > retrieved:
        raise ValueError("future_dataset_asof")
    if manifest["event_timestamp_policy"] != "independently_verified":
        raise ValueError("unverified_event_timestamp_policy")
    return {
        "dataset_id": manifest["dataset_id"],
        "market": manifest["market"],
        "survivorship_warning": not manifest["includes_delisted"],
        "license_warning": not manifest["license_reviewed"],
        "research_comparison_eligible": (
            manifest["includes_delisted"] and manifest["license_reviewed"]),
        "trade_ready": False,
    }
