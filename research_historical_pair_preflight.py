"""Offline provenance-gated research preparation; no network or trading.

Structural CSV acceptance is not proof of source authenticity, licensing,
historical point-in-time availability, or survivorship-bias control.
"""
from research_historical_price_ingest_gate import audit_historical_price_dataset


def prepare_historical_research_pair(stock_manifest, stock_payload,
                                     benchmark_manifest, benchmark_payload):
    """Audit two independent input files without silently certifying either."""
    if stock_payload == benchmark_payload:
        raise ValueError("identical_stock_and_benchmark_payload")
    stock = audit_historical_price_dataset(stock_manifest, stock_payload)
    benchmark = audit_historical_price_dataset(benchmark_manifest, benchmark_payload)
    if not stock["accepted"] or not benchmark["accepted"]:
        raise ValueError("historical_input_not_structurally_accepted")
    return {
        "stock": stock,
        "benchmark": benchmark,
        "distinct_payloads": True,
        "distinct_providers_verified": False,
        "benchmark_independence_verified": False,
        "historical_market_validation_completed": False,
        "source_license_verified": False,
        "point_in_time_verified": False,
        "research_data_ready": False,
        "trade_ready": False,
    }
