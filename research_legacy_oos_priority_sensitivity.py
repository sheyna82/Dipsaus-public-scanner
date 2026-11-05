"""Same-day priority sensitivity of legacy OOS capacity comparisons.

Compare neutral, pre-outcome ordering variants; never rank by realized return.
These are descriptive simulations, not proof of an investment edge.
"""
from research_legacy_oos_source_binding import prepare_legacy_oos_source_bound_ledger
from research_source_bound_tranche_comparison import compare_source_bound_tranches


def compare_legacy_oos_same_day_priority(legacy_rows, source_bytes, *,
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
        retrieved_at_utc=retrieved_at_utc, legacy_cost_bps=legacy_cost_bps,
        simulator_round_trip_cost_rate=simulator_round_trip_cost_rate)
    if not prepared["legacy_fee_model_equivalent_to_simulator"]:
        raise ValueError("LEGACY_SIMULATOR_COST_MODEL_MISMATCH")
    base = prepared["ledger"]
    results = {}
    for mode in ("symbol_asc", "symbol_desc"):
        ordered = sorted(base["candidates"],
                         key=lambda c: (c["entry_date"],
                                        c["symbol"] if mode == "symbol_asc"
                                        else tuple(-ord(char) for char in c["symbol"])))
        payload = {**base, "candidates": ordered}
        comparison = compare_source_bound_tranches(
            payload, source_bytes,
            starting_settled_cash_eur=starting_settled_cash_eur,
            tranches_eur=tranches_eur, max_positions=max_positions,
            settlement_business_days=settlement_business_days,
            settlement_holidays=settlement_holidays,
            round_trip_cost_rate=simulator_round_trip_cost_rate)
        results[mode] = comparison["comparison"]["scenarios"]
    sensitivity = []
    for i, tranche in enumerate(tranches_eur):
        asc, desc = results["symbol_asc"][i], results["symbol_desc"][i]
        sensitivity.append({
            "tranche_eur": tranche,
            "same_day_priority_changes_accepted_candidates":
                asc["accepted_candidate_ids"] != desc["accepted_candidate_ids"],
            "accepted_count_range": [min(asc["accepted_count"], desc["accepted_count"]),
                                     max(asc["accepted_count"], desc["accepted_count"])],
            "symbol_asc": asc, "symbol_desc": desc,
        })
    return {
        "status": "RESEARCH_ONLY_SAME_DAY_PRIORITY_SENSITIVITY",
        "candidate_count": len(base["candidates"]),
        "source_snapshot_sha256": prepared["source_snapshot_sha256"],
        "source_snapshot_bytes_verified": True,
        "candidates_rederived_from_snapshot": False,
        "priority_modes": ["symbol_asc", "symbol_desc"],
        "sensitivity": sensitivity,
        "outcomes_independently_verified": False,
        "historical_edge_proven": False,
        "trade_ready": False,
    }
