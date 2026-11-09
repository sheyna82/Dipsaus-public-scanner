"""Admission-controlled offline entry point for European relative-strength research.

Existing historical compare() remains unchanged for reproducibility.
New research calculations should use this wrapper; never a live scanner path.
"""
from research_benchmark_source_admission import assess_source
from research_europe_relative_strength import compare, PAIRS

def compare_admitted(europe, benchmarks, identity_evidence, as_of_complete_day, source_receipts):
    if not isinstance(source_receipts, dict):
        raise ValueError("MISSING_BENCHMARK_SOURCE_RECEIPTS")
    required = set(PAIRS.values()) | {"STOXX600_PRICE"}
    if set(source_receipts) != required:
        raise ValueError("INCOMPLETE_BENCHMARK_SOURCE_RECEIPTS")
    for benchmark in sorted(required):
        receipt = source_receipts[benchmark]
        if not isinstance(receipt, dict) or receipt.get("source_id") != benchmark:
            raise ValueError("BENCHMARK_SOURCE_ID_MISMATCH:" + benchmark)
        decision = assess_source(receipt)
        if not decision["research_calculation_eligible"]:
            raise ValueError("BENCHMARK_SOURCE_NOT_ADMITTED:" + benchmark +
                             ":" + ",".join(decision["unmet_requirements"]))
    return compare(europe, benchmarks, identity_evidence, as_of_complete_day)
