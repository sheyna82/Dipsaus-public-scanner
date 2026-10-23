"""Offline provenance-gated research preparation; no network or trading.

Structural CSV acceptance is not proof of source authenticity, licensing,
historical point-in-time availability, or survivorship-bias control.
"""
from research_historical_price_ingest_gate import audit_historical_price_dataset
import csv
import io
from decimal import Decimal, InvalidOperation
from datetime import date


def prepare_historical_research_pair(stock_manifest, stock_payload,
                                     benchmark_manifest, benchmark_payload,
                                     as_of_date=None):
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
    # Calendar age is descriptive only. Weekends, exchange holidays and
    # vendor publication delays require an authenticated market calendar.
    def calendar_age(closes):
        if as_of_date is None:
            return None
        reference = date.fromisoformat(as_of_date)
        last = date.fromisoformat(max(closes))
        if last > reference:
            raise ValueError("historical_last_date_after_as_of_date")
        return (reference - last).days

    stock_calendar_age = calendar_age(stock_closes)
    benchmark_closes = close_by_date(benchmark_payload)
    benchmark_calendar_age = calendar_age(benchmark_closes)
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
    possible_shared_intervals = max(0, len(ordered_shared) - 1)
    skipped_shared_date_gaps = possible_shared_intervals - len(comparable_pairs)
    comparable_interval_coverage = (
        len(comparable_pairs) / possible_shared_intervals
        if possible_shared_intervals else None)
    # Count consecutive unavailable shared intervals; clustering is diagnostic
    # only and does not certify any price source.
    current_missing_run = 0
    longest_missing_run = 0
    missing_run_count = 0
    missing_run_positions = []
    current_run_start = None
    for index, pair in enumerate(zip(ordered_shared, ordered_shared[1:])):
        if pair not in comparable_pairs:
            if current_run_start is None:
                current_run_start = index
            current_missing_run += 1
            longest_missing_run = max(longest_missing_run, current_missing_run)
        elif current_missing_run:
            missing_run_count += 1
            missing_run_positions.append((current_run_start, index - 1))
            current_missing_run = 0
            current_run_start = None
    if current_missing_run:
        missing_run_count += 1
        missing_run_positions.append((current_run_start, possible_shared_intervals - 1))
    missing_intervals_at_start = (
        missing_run_positions[0][1] + 1
        if missing_run_positions and missing_run_positions[0][0] == 0 else 0)
    missing_intervals_at_end = (
        possible_shared_intervals - missing_run_positions[-1][0]
        if missing_run_positions and
        missing_run_positions[-1][1] == possible_shared_intervals - 1 else 0)
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
    # Require substantial calendar coverage as well as enough observations.
    # This 80% screening threshold is provisional and not calibrated.
    minimum_comparable_interval_coverage = 0.8
    return_coverage_sufficient = (
        comparable_interval_coverage is not None and
        comparable_interval_coverage >= minimum_comparable_interval_coverage)
    # A long contiguous missing block can hide a regime shift despite
    # adequate overall coverage. Threshold is provisional, research-only.
    maximum_missing_interval_run_for_screening = 3
    missing_run_sufficient_for_screening = (
        longest_missing_run <= maximum_missing_interval_run_for_screening)
    return_pattern_screening_match = (
        return_overlap_sufficient and return_coverage_sufficient and
        missing_run_sufficient_for_screening and
        matching_return_intervals == comparable_return_intervals)
    same_provider_claim = (stock_manifest["provider"].strip().casefold() ==
                           benchmark_manifest["provider"].strip().casefold())
    same_source_url_claim = (stock_manifest["source_url"].strip() ==
                             benchmark_manifest["source_url"].strip())
    return {
        "stock_last_price_date": max(stock_closes),
        "benchmark_last_price_date": max(benchmark_closes),
        "as_of_date": as_of_date,
        "stock_last_price_calendar_age_days": stock_calendar_age,
        "benchmark_last_price_calendar_age_days": benchmark_calendar_age,
        "exchange_session_freshness_verified": False,
        "stock_price_dates": len(stock_closes),
        "benchmark_price_dates": len(benchmark_closes),
        "shared_price_dates": len(shared_dates),
        "comparable_shared_return_intervals": comparable_return_intervals,
        "skipped_nonadjacent_shared_intervals": skipped_shared_date_gaps,
        "longest_nonadjacent_shared_interval_run": longest_missing_run,
        "nonadjacent_shared_interval_run_count": missing_run_count,
        "missing_shared_intervals_at_start": missing_intervals_at_start,
        "missing_shared_intervals_at_end": missing_intervals_at_end,
        "possible_shared_return_intervals": possible_shared_intervals,
        "comparable_interval_coverage_fraction": comparable_interval_coverage,
        "minimum_comparable_return_intervals": minimum_comparable_intervals,
        "return_overlap_sufficient_for_screening": return_overlap_sufficient,
        "insufficient_return_overlap": not return_overlap_sufficient,
        "return_pattern_screening_match": return_pattern_screening_match,
        "minimum_comparable_interval_coverage": minimum_comparable_interval_coverage,
        "return_coverage_sufficient_for_screening": return_coverage_sufficient,
        "maximum_missing_interval_run_for_screening": maximum_missing_interval_run_for_screening,
        "missing_run_sufficient_for_screening": missing_run_sufficient_for_screening,
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
