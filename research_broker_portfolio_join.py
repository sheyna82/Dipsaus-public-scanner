"""Research-only joined broker evidence and portfolio reconciliation."""
from research_broker_evidence import assess_broker_evidence
from research_portfolio_snapshot import reconcile_broker_positions


def reconcile_with_broker_evidence(config, evidence, *, now_utc, max_age_hours=24,
                                   configured_instruments=None, broker_instruments=None):
    """Preserve all uncertainty: source claims never authorize capacity or trading."""
    assessment = assess_broker_evidence(evidence, now_utc=now_utc,
                                        max_age_hours=max_age_hours)
    comparison = reconcile_broker_positions(
        config, evidence["positions"],
        as_of_utc=evidence["captured_at_utc"],
        now_utc=now_utc,
        max_age_hours=max_age_hours,
        complete_account_snapshot=evidence["positions_complete"],
        configured_instruments=configured_instruments,
        broker_instruments=broker_instruments)
    return {
        "status": "RESEARCH_ONLY_JOINED_BROKER_REVIEW",
        "evidence": assessment,
        "portfolio_comparison": comparison,
        "open_orders_completeness_claim": assessment["orders_complete_claim"],
        "open_orders_observed_count": assessment["observed_open_order_count"],
        "open_orders_independently_verified": False,
        "broker_identity_authenticated": False,
        "positions_independently_verified": False,
        "actual_cash_eur": None,
        "actual_remaining_slots": None,
        "portfolio_capacity_usable": False,
        "trade_ready": False,
        "automatic_orders": False,
    }
