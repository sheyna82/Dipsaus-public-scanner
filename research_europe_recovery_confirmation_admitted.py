"""Fail-closed research-only recovery confirmation entry point.

Legacy evaluate() remains unchanged for historical reproducibility.
"""
from research_benchmark_source_admission import assess_source
from research_europe_relative_strength_admitted import (
    TRUSTED_SOURCE_RECEIPT_SHA256, receipt_digest,
)
from research_europe_recovery_confirmation import evaluate

def evaluate_admitted(history, as_of_complete_day, benchmark_name, source_receipt):
    if not isinstance(benchmark_name, str) or not benchmark_name.strip():
        raise ValueError("INVALID_BENCHMARK_NAME")
    if not isinstance(source_receipt, dict) or source_receipt.get("source_id") != benchmark_name:
        raise ValueError("BENCHMARK_SOURCE_ID_MISMATCH")
    decision = assess_source(source_receipt)
    if not decision["research_calculation_eligible"]:
        raise ValueError("BENCHMARK_SOURCE_NOT_ADMITTED:" + benchmark_name)
    if TRUSTED_SOURCE_RECEIPT_SHA256.get(benchmark_name) != receipt_digest(source_receipt):
        raise ValueError("BENCHMARK_SOURCE_RECEIPT_NOT_TRUSTED:" + benchmark_name)
    return evaluate(history, as_of_complete_day, benchmark_identity_verified=True)
