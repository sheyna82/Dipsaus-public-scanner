"""Offline legacy OOS -> source-bound capacity bridge, without evidence inflation.

A matching source digest does NOT prove the legacy outcomes were derived from
the bytes. All reported outcomes remain unverified research observations.
"""
from research_legacy_oos_source_binding import prepare_legacy_oos_source_bound_ledger
from research_source_bound_tranche_comparison import compare_source_bound_tranches


def compare_legacy_oos_capital(legacy_rows, source_bytes, *,
                               source_name, retrieved_at_utc,
                               starting_settled_cash_eur,
                               legacy_cost_bps=50,
                               simulator_round_trip_cost_rate=0.005,
                               tranches_eur=(3500, 5000, 7500, 10000),
                               max_positions=6,
                               settlement_business_days=2,
                               settlement_holidays=()):
    prepared = prepare_legacy_oos_source_bound_ledger(
        legacy_rows, source_bytes, source_name=source_name,
        retrieved_at_utc=retrieved_at_utc,
        legacy_cost_bps=legacy_cost_bps,
        simulator_round_trip_cost_rate=simulator_round_trip_cost_rate)
    if not prepared["legacy_fee_model_equivalent_to_simulator"]:
        raise ValueError("LEGACY_SIMULATOR_COST_MODEL_MISMATCH")
    result = compare_source_bound_tranches(
        prepared["ledger"], source_bytes,
        starting_settled_cash_eur=starting_settled_cash_eur,
        tranches_eur=tranches_eur, max_positions=max_positions,
        settlement_business_days=settlement_business_days,
        settlement_holidays=settlement_holidays,
        round_trip_cost_rate=simulator_round_trip_cost_rate)
    return {
        "status": "RESEARCH_ONLY_LEGACY_OOS_CAPACITY_BRIDGE",
        "source_snapshot_sha256": prepared["source_snapshot_sha256"],
        "candidate_sha256": prepared["candidate_sha256"],
        "candidate_count": result["candidate_count"],
        "source_snapshot_bytes_verified": True,
        "candidates_rederived_from_snapshot": False,
        "source_independently_verified": False,
        "outcomes_independently_verified": False,
        "legacy_fee_model_equivalent_to_simulator": prepared["legacy_fee_model_equivalent_to_simulator"],
        "historical_edge_proven": False,
        "trade_ready": False,
        "comparison": result["comparison"],
    }
