"""Research-only, actionable evidence gaps; never emits a trade recommendation."""
from research_broker_portfolio_join import reconcile_with_broker_evidence


def portfolio_evidence_gap_report(config, evidence, *, now_utc, max_age_hours=24,
                                  configured_instruments=None, broker_instruments=None):
    joined = reconcile_with_broker_evidence(
        config, evidence, now_utc=now_utc, max_age_hours=max_age_hours,
        configured_instruments=configured_instruments,
        broker_instruments=broker_instruments)
    source = joined["evidence"]
    comparison = joined["portfolio_comparison"]
    gaps = []
    def add(code, detail):
        gaps.append({"code": code, "detail": detail})
    if not source["fresh"]:
        add("STALE_BROKER_EVIDENCE", "A newer broker observation is required.")
    if not source["positions_complete_claim"]:
        add("INCOMPLETE_POSITIONS", "The supplied positions are explicitly partial.")
    if not source["orders_complete_claim"]:
        add("INCOMPLETE_OPEN_ORDERS", "The supplied open orders are explicitly partial.")
    add("UNAUTHENTICATED_SOURCE", "Broker source and account scope are unverified claims.")
    add("UNVERIFIED_COMPLETENESS", "No independent proof of account-wide coverage.")
    if comparison["position_mismatches"]:
        add("POSITION_MISMATCH", "Configured and observed quantities differ; inspect details.")
    if comparison["possible_symbol_aliases_review_only"]:
        add("SYMBOL_ALIAS_REVIEW", "Ticker similarity cannot establish instrument identity.")
    if any(x["status"] != "METADATA_MATCH_UNAUTHENTICATED"
           for x in comparison["instrument_identity_reviews"]):
        add("INSTRUMENT_IDENTITY_INCOMPLETE", "Instrument metadata is absent or conflicting.")
    if source["observed_open_order_count"]:
        add("OPEN_ORDERS_REQUIRE_REVIEW", "Observed open orders may affect buying power.")
    add("CASH_NOT_VERIFIED", "Actual available broker cash and reservations are unknown.")
    return {
        "status": "RESEARCH_ONLY_EVIDENCE_GAP_REPORT",
        "gap_codes": [g["code"] for g in gaps],
        "evidence_gaps": gaps,
        "joined_review": joined,
        "capacity_usable": False,
        "trade_ready": False,
        "automatic_orders": False,
    }
