"""Offline-only provenance audit reusing the existing point-in-time gate.

The supplied metadata is not independently authenticated. This is NOT proof
that a capture existed before subsequent market outcomes.
"""
from research_point_in_time_availability_gate import assess_point_in_time_record


def audit_capture_provenance(capture, source_records):
    if not isinstance(capture, dict) or not isinstance(source_records, dict):
        raise ValueError("INVALID_PROVENANCE_INPUT")
    symbols = capture.get("sample_symbols")
    observed = capture.get("observed_at_utc")
    if not isinstance(symbols, list) or not symbols or len(symbols) != len(set(symbols)):
        raise ValueError("INVALID_SAMPLE")
    if set(source_records) != set(symbols):
        raise ValueError("PROVENANCE_COVERAGE_MISMATCH")
    results = {}
    for symbol in sorted(symbols):
        record = source_records[symbol]
        if not isinstance(record, dict) or not isinstance(record.get("provider"), str) or not record["provider"].strip():
            raise ValueError("INVALID_PROVIDER_METADATA")
        outcome = assess_point_in_time_record(record, decision_at=observed)
        results[symbol] = {"accepted": outcome["accepted"], "reasons": outcome["reasons"],
                           "provider": record["provider"], "source_authenticity_verified": False}
    return {"research_only": True, "trade_ready": False,
            "metadata_chronology_accepted": all(v["accepted"] for v in results.values()),
            "independent_prospective_proof": False, "symbols": results}
