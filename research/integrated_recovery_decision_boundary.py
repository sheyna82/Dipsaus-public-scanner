"""Research-only recovery decision boundary. Broker screen is necessary, never sufficient."""
from integrated_broker_candidate_screen import screen_candidates

def assess(config, broker_evidence, recovery_candidates, protocol_verified=False,
           point_in_time_data_verified=False, portfolio_reconciled=False):
    if not all(isinstance(flag, bool) for flag in
               (protocol_verified, point_in_time_data_verified, portfolio_reconciled)):
        raise ValueError("INVALID_EVIDENCE_FLAGS")
    broker = screen_candidates(config, broker_evidence, recovery_candidates)
    rows = []
    for candidate in broker["candidates"]:
        missing = []
        if not candidate["broker_eligible"]:
            missing.append("DEGIRO_INSTRUMENT_NOT_VERIFIED")
        if not protocol_verified:
            missing.append("FROZEN_PROTOCOL_NOT_VERIFIED")
        if not point_in_time_data_verified:
            missing.append("POINT_IN_TIME_MARKET_DATA_NOT_VERIFIED")
        if not portfolio_reconciled:
            missing.append("PORTFOLIO_NOT_RECONCILED")
        rows.append({"symbol": candidate["symbol"], "research_screen_allowed": not missing,
                     "missing_evidence": missing, "trade_ready": False,
                     "status": "RESEARCH_SCREEN_ELIGIBLE_NOT_TRADE_APPROVED"
                     if not missing else "BLOCKED_MISSING_EVIDENCE"})
    return {"status": "RESEARCH_ONLY_RECOVERY_DECISION_BOUNDARY",
            "trade_ready": False, "live_scanner_changed": False, "candidates": rows}
