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
        "trade_ready": False,
    }
