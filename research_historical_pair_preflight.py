"""Offline provenance-gated research preparation; no network or trading.

Structural CSV acceptance is not proof of source authenticity, licensing,
historical point-in-time availability, or survivorship-bias control.
"""
from research_historical_price_ingest_gate import audit_historical_price_dataset
import csv
import io
from decimal import Decimal, InvalidOperation


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
        try:
            return {row["date"]: Decimal(row["close"].strip()) for row in rows}
        except (InvalidOperation, TypeError) as exc:
            raise ValueError("invalid_close_value") from exc

    stock_closes = close_by_date(stock_payload)
    benchmark_closes = close_by_date(benchmark_payload)
    shared_dates = stock_closes.keys() & benchmark_closes.keys()
    matching_closes = sum(stock_closes[day] == benchmark_closes[day]
                          for day in shared_dates)
    stock_only_dates = len(stock_closes) - len(shared_dates)
    benchmark_only_dates = len(benchmark_closes) - len(shared_dates)
    # Compare scale-invariant consecutive close returns only where both
    # instruments have the same adjacent observed dates. This is a diagnostic,
    # not proof of duplicate provenance or independent sources.
    ordered_shared = sorted(shared_dates)
    def adjacent_pairs(closes):
        dates = sorted(closes)
        return set(zip(dates, dates[1:]))

    comparable_pairs = adjacent_pairs(stock_closes) & adjacent_pairs(benchmark_closes)
    skipped_shared_date_gaps = max(0, len(ordered_shared) - 1) - len(comparable_pairs)
    comparable_return_intervals = 0
    matching_return_intervals = 0
    for previous, current in sorted(comparable_pairs):
        if (stock_closes[previous] <= 0 or benchmark_closes[previous] <= 0):
            continue
        comparable_return_intervals += 1
        if (stock_closes[current] / stock_closes[previous] ==
                benchmark_closes[current] / benchmark_closes[previous]):
            matching_return_intervals += 1
    # A short or sparse overlap cannot support a strong duplication inference.
    # Thresholds are diagnostics, not a claim of statistically validated power.
    minimum_comparable_intervals = 20
    return_overlap_sufficient = comparable_return_intervals >= minimum_comparable_intervals
    # Distinguish a diagnostic match from a sufficiently long screening match.
    # Neither outcome verifies provenance or independence.
    return_match_fraction = (
        matching_return_intervals / comparable_return_intervals
        if comparable_return_intervals else None)
    return_pattern_screening_match = (
        return_overlap_sufficient and
        matching_return_intervals == comparable_return_intervals)
    same_provider_claim = (stock_manifest["provider"].strip().casefold() ==
                           benchmark_manifest["provider"].strip().casefold())
    same_source_url_claim = (stock_manifest["source_url"].strip() ==
                             benchmark_manifest["source_url"].strip())
    return {
        "stock_price_dates": len(stock_closes),
        "benchmark_price_dates": len(benchmark_closes),
        "shared_price_dates": len(shared_dates),
        "comparable_shared_return_intervals": comparable_return_intervals,
        "skipped_nonadjacent_shared_intervals": skipped_shared_date_gaps,
        "minimum_comparable_return_intervals": minimum_comparable_intervals,
        "return_overlap_sufficient_for_screening": return_overlap_sufficient,
        "insufficient_return_overlap": not return_overlap_sufficient,
        "return_pattern_screening_match": return_pattern_screening_match,
        "matching_shared_return_intervals": matching_return_intervals,
        "matching_shared_return_fraction": return_match_fraction,
        "all_comparable_shared_returns_match": (
            comparable_return_intervals > 0 and
            matching_return_intervals == comparable_return_intervals),
        "stock_only_price_dates": stock_only_dates,
        "benchmark_only_price_dates": benchmark_only_dates,
        "stock_date_overlap_fraction": len(shared_dates) / len(stock_closes),
        "benchmark_date_overlap_fraction": len(shared_dates) / len(benchmark_closes),
        "partial_price_date_overlap": bool(shared_dates) and (stock_only_dates > 0 or benchmark_only_dates > 0),
        "no_overlapping_price_dates": not bool(shared_dates),
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
