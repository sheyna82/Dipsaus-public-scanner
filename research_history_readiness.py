"""Research-only readiness gate for supplied historical candidate universes.

The gate does not authenticate a universe or sources; even a fully covered
supplied sample cannot be promoted to a validated historical backtest.
"""
from research_historical_coverage import audit_historical_coverage

BLOCKED = {"trade_ready": False, "order_placement_enabled": False,
           "source_authenticity_independently_verified": False}

def assess_history_readiness(signals, outcomes):
    coverage = audit_historical_coverage(signals, outcomes)
    if coverage["status"] != "HISTORICAL_COVERAGE_RESEARCH_ONLY":
        return {**BLOCKED, "status": "HISTORY_READINESS_BLOCKED",
                "reason": coverage.get("reason"), "coverage": coverage,
                "backtest_validated": False}
    if not coverage["signals"]:
        reason = "EMPTY_SIGNAL_UNIVERSE"
    elif coverage["missing_outcome_ids"]:
        reason = "MISSING_HISTORICAL_OUTCOMES"
    elif not coverage["decision_counts"]["REJECTED"]:
        reason = "NO_REJECTED_SIGNALS_REPRESENTED"
    else:
        reason = "UNIVERSE_AND_PROVENANCE_UNVERIFIED"
    return {**BLOCKED, "status": "HISTORY_READINESS_BLOCKED",
            "reason": reason, "coverage": coverage,
            "backtest_validated": False,
            "complete_candidate_universe_verified": False,
            "note": "A full supplied sample does not prove historical capture completeness."}
