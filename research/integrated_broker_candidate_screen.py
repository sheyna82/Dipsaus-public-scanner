"""Fail-closed broker gate in research candidate selection; no live scanner imports."""
from integrated_degiro_eligibility_gate import evaluate

def screen_candidates(config, broker_evidence, recovery_candidates):
    broker = evaluate(config, broker_evidence)
    eligibility = {row["symbol"]: row["eligible_for_recovery_screen"]
                   for row in broker["candidates"]}
    screened = []
    seen = set()
    for candidate in recovery_candidates:
        symbol = candidate["symbol"]
        if symbol in seen:
            raise ValueError("DUPLICATE_RECOVERY_CANDIDATE:" + symbol)
        seen.add(symbol)
        if candidate.get("trade_ready") is not False:
            raise ValueError("RECOVERY_CANDIDATE_MUST_BE_RESEARCH_ONLY:" + symbol)
        eligible = eligibility.get(symbol, False)
        screened.append({"symbol": symbol, "broker_eligible": eligible,
                         "research_screen_allowed": eligible,
                         "trade_ready": False,
                         "reason": "BROKER_EVIDENCE_VERIFIED" if eligible
                                   else "BROKER_UNVERIFIED_OR_UNSUPPORTED"})
    return {"status": "RESEARCH_ONLY_BROKER_PRESELECTION",
            "trade_ready": False, "candidates": screened}
