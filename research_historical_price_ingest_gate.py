"""Offline ingestion entry point: hash and OHLCV checks must both pass."""
from research_historical_source_manifest import audit_historical_source_manifest
from research_daily_price_csv_audit import audit_daily_price_csv


def audit_historical_price_dataset(manifest, payload):
    """Structural-only acceptance; never certifies provenance or PIT replay."""
    source = audit_historical_source_manifest(manifest, payload)
    prices = audit_daily_price_csv(payload)
    return {
        "accepted": source["accepted"] and prices["accepted"],
        "rows": prices["rows"],
        "payload_sha256": source["payload_sha256"],
        "manifest_consistent": source["manifest_consistent"],
        "ohlcv_structure_valid": prices["accepted"],
        "provider_authenticity_verified": False,
        "license_verified": False,
        "point_in_time_verified": False,
        "corporate_actions_verified": False,
        "delisted_symbols_coverage_verified": False,
        "survivorship_bias_control_verified": False,
        "benchmark_independence_verified": False,
        "research_data_ready": False,
        "requires_external_license_review": True,
        "requires_external_provenance_review": True,
        "requires_point_in_time_reconstruction": True,
        "requires_corporate_action_review": True,
        "requires_delisting_coverage_review": True,
        "requires_survivorship_bias_review": True,
        "requires_independent_benchmark_review": True,
        "trade_ready": False,
    }
