"""Offline, explicit event-study data readiness manifest.

No live downloads or predictions. Missing real data is reported as missing,
not silently replaced with synthetic examples.
"""
from research_event_opportunity_cohort import EVENT_COHORT

REQUIRED_ARTIFACTS = (
    "issuer_event_confirmation",
    "pre_event_stock_prices",
    "pre_event_benchmark_prices",
    "post_event_stock_prices",
    "post_event_benchmark_prices",
    "verified_exchange_sessions",
    "market_data_payload_digest",
    "release_timestamp_confirmation",
)


def build_event_data_manifest(artifacts_by_symbol=None):
    supplied = {} if artifacts_by_symbol is None else artifacts_by_symbol
    if not isinstance(supplied, dict):
        raise ValueError("artifacts_must_be_mapping")
    records = []
    for symbol, event_date in EVENT_COHORT:
        artifacts = supplied.get(symbol, {})
        if not isinstance(artifacts, dict):
            raise ValueError("symbol_artifacts_must_be_mapping")
        missing = [name for name in REQUIRED_ARTIFACTS
                   if not isinstance(artifacts.get(name), dict)
                   or artifacts[name].get("verified") is not True]
        records.append({
            "symbol": symbol,
            "event_date": event_date,
            "missing_verified_artifacts": missing,
            "verified_artifact_count": len(REQUIRED_ARTIFACTS) - len(missing),
            "data_ready": not missing,
            "independent_review_completed": False,
            "predictive_skill_established": False,
            "trade_ready": False,
        })
    return {
        "cohort": "event_notifications_2026_10_24",
        "required_artifacts": list(REQUIRED_ARTIFACTS),
        "records": records,
        "real_data_collected_by_this_module": False,
        "live_notifications_enabled": False,
        "automatic_orders": False,
    }
