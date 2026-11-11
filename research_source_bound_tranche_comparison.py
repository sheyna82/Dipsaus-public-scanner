"""Offline, source-bound capital comparison; structural and byte integrity only.

Never infer independently validated market data, execution or alpha.
"""
from research_historical_candidate_ledger import verify_historical_source_snapshot
from research_tranche_capacity_comparison import compare_tranche_capacity


def compare_source_bound_tranches(payload, source_bytes, *,
                                  starting_settled_cash_eur,
                                  tranches_eur=(3500, 5000, 7500, 10000),
                                  max_positions=6,
                                  settlement_business_days=2,
                                  settlement_holidays=(),
                                  round_trip_cost_rate=0.005):
    """Fail closed before any capital simulation if source bytes mismatch."""
    verified = verify_historical_source_snapshot(payload, source_bytes)
    if not verified["candidates"]:
        raise ValueError("EMPTY_HISTORICAL_CANDIDATE_LEDGER")
    comparison = compare_tranche_capacity(
        verified["candidates"],
        starting_settled_cash_eur=starting_settled_cash_eur,
        tranches_eur=tranches_eur,
        max_positions=max_positions,
        settlement_business_days=settlement_business_days,
        settlement_holidays=settlement_holidays,
        round_trip_cost_rate=round_trip_cost_rate)
    return {
        "status": "RESEARCH_ONLY_SOURCE_BOUND_CAPACITY",
        "source_snapshot_sha256": verified["source_snapshot_sha256"],
        "source_snapshot_bytes_verified": True,
        "candidate_sha256": verified["candidate_sha256"],
        "candidate_count": verified["candidate_count"],
        "source_independently_verified": False,
        "outcomes_independently_verified": False,
        "historical_edge_proven": False,
        "trade_ready": False,
        "comparison": comparison,
    }
