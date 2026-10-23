"""Offline provenance-gated research preparation; no network or trading.

Structural CSV acceptance is not proof of source authenticity, licensing,
historical point-in-time availability, or survivorship-bias control.
"""
from research_historical_price_ingest_gate import audit_historical_price_dataset
import csv
import io


def prepare_historical_research_pair(stock_manifest, stock_payload,
                                     benchmark_manifest, benchmark_payload):
    """Audit two independent input files without silently certifying either."""
    if stock_payload == benchmark_payload:
        raise ValueError("identical_stock_and_benchmark_payload")
    stock = audit_historical_price_dataset(stock_manifest, stock_payload)
    benchmark = audit_historical_price_dataset(benchmark_manifest, benchmark_payload)
    if not stock["accepted"] or not benchmark["accepted"]:
        raise ValueError("historical_input_not_structurally_accepted")
    def close_by_date(payload):
        text = payload.decode("utf-8-sig")
        rows = csv.DictReader(io.StringIO(text))
        return {row["date"]: row["close"].strip() for row in rows}

    stock_closes = close_by_date(stock_payload)
    benchmark_closes = close_by_date(benchmark_payload)
    shared_dates = stock_closes.keys() & benchmark_closes.keys()
    matching_closes = sum(stock_closes[day] == benchmark_closes[day]
                          for day in shared_dates)
    same_provider_claim = (stock_manifest["provider"].strip().casefold() ==
                           benchmark_manifest["provider"].strip().casefold())
    same_source_url_claim = (stock_manifest["source_url"].strip() ==
                             benchmark_manifest["source_url"].strip())
    return {
        "shared_price_dates": len(shared_dates),
        "matching_close_values_on_shared_dates": matching_closes,
        "all_shared_close_values_match": bool(shared_dates) and matching_closes == len(shared_dates),
        "same_declared_provider": same_provider_claim,
        "same_declared_source_url": same_source_url_claim,
        "provider_claims_independence": not same_provider_claim,
        "stock": stock,
        "benchmark": benchmark,
        "distinct_payloads": True,
        "distinct_providers_verified": False,
        "provider_claims_authenticated": False,
        "benchmark_independence_verified": False,
        "historical_market_validation_completed": False,
        "source_license_verified": False,
        "point_in_time_verified": False,
        "research_data_ready": False,
        "trade_ready": False,
    }
