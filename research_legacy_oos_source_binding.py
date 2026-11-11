"""Offline legacy OOS conversion bound to immutable raw source snapshot bytes.

This does not certify that old candidates were actually derived from source.
It records their claimed relation, verifies exact source byte digest, and
converts old net return convention without silently double charging costs.
"""
import hashlib
from research_legacy_oos_return_adapter import adapt_legacy_oos_net_candidates
from research_historical_candidate_ledger import verify_historical_source_snapshot


def prepare_legacy_oos_source_bound_ledger(legacy_rows, source_bytes, *,
                                           source_name, retrieved_at_utc,
                                           legacy_cost_bps=50,
                                           simulator_round_trip_cost_rate=0.005):
    if not isinstance(source_bytes, bytes) or not source_bytes:
        raise ValueError("INVALID_FROZEN_SOURCE_BYTES")
    if not isinstance(source_name, str) or not source_name.strip():
        raise ValueError("MISSING_SOURCE_NAME")
    if not isinstance(retrieved_at_utc, str) or not retrieved_at_utc.strip():
        raise ValueError("MISSING_SOURCE_TIMESTAMP")
    converted = adapt_legacy_oos_net_candidates(
        legacy_rows, legacy_cost_bps=legacy_cost_bps,
        simulator_round_trip_cost_rate=simulator_round_trip_cost_rate)
    if not converted["candidates"]:
        raise ValueError("EMPTY_LEGACY_OOS_CANDIDATES")
    payload = {
        "format": "DIPSAUS_HISTORICAL_CANDIDATES_V1",
        "provenance": {
            "source": source_name.strip(),
            "retrieved_at_utc": retrieved_at_utc,
            "source_snapshot_sha256": hashlib.sha256(source_bytes).hexdigest()},
        "candidates": converted["candidates"],
    }
    validated = verify_historical_source_snapshot(payload, source_bytes)
    return {
        "status": "RESEARCH_ONLY_LEGACY_SOURCE_BOUND_LEDGER",
        "ledger": payload,
        "candidate_sha256": validated["candidate_sha256"],
        "source_snapshot_sha256": validated["source_snapshot_sha256"],
        "source_snapshot_bytes_verified": validated["source_snapshot_bytes_verified"],
        "legacy_fee_model_equivalent_to_simulator": converted["legacy_fee_model_equivalent_to_simulator"],
        "legacy_cost_bps": legacy_cost_bps,
        "simulator_round_trip_cost_rate": simulator_round_trip_cost_rate,
        "candidates_rederived_from_snapshot": False,
        "source_independently_verified": False,
        "outcomes_independently_verified": False,
        "trade_ready": False,
    }
