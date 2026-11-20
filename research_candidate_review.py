"""Offline research composition of ranking and risk flags; no trading decisions."""
from research_candidate_ranking import rank_research_candidates
from research_liquidity_earnings_risk import screen_research_risks

BLOCKED = {"trade_ready": False, "order_placement_enabled": False,
           "source_authenticity_independently_verified": False}

def review_research_candidates(candidates):
    if not isinstance(candidates, list):
        return {**BLOCKED, "status": "REVIEW_INPUT_BLOCKED", "reason": "NOT_A_LIST",
                "candidates": []}
    if any(not isinstance(c, dict) or not isinstance(c.get("risk_inputs"), dict)
           for c in candidates):
        return {**BLOCKED, "status": "REVIEW_INPUT_BLOCKED",
                "reason": "MISSING_RISK_INPUTS", "candidates": []}
    ranked = rank_research_candidates(candidates)
    if ranked["status"] != "RESEARCH_RANKING_ONLY":
        return {**BLOCKED, "status": "REVIEW_INPUT_BLOCKED",
                "reason": ranked.get("reason"), "candidates": []}
    risks = {c["id"]: screen_research_risks(c["risk_inputs"]) for c in candidates}
    output = []
    for candidate in ranked["candidates"]:
        risk = risks[candidate["id"]]
        rank_ok = candidate["status"] == "PROVISIONAL_RESEARCH_RANK"
        risk_ok = risk["status"] == "RESEARCH_RISK_SCREEN_ONLY"
        reviewable = (rank_ok and risk_ok and
                      risk["research_priority"] == "ELIGIBLE_FOR_FURTHER_RESEARCH")
        if not rank_ok:
            disposition = "NOT_RANKABLE_OR_FINANCIAL_GATE_FAILED"
        elif not risk_ok:
            disposition = "RISK_DATA_BLOCKED"
        elif risk["research_priority"] == "DEFER_FOR_REVIEW":
            disposition = "RISK_WARNING_REVIEW"
        elif risk["research_priority"] == "REVIEW_EARNINGS_UNKNOWN":
            disposition = "EARNINGS_UNKNOWN_REVIEW"
        else:
            disposition = "RESEARCH_REVIEW_CANDIDATE"
        output.append({**candidate, **BLOCKED, "risk_screen": risk,
                       "research_disposition": disposition,
                       "eligible_for_further_research": reviewable})
    # Scores are retained for comparison, but warnings always remain visible.
    return {**BLOCKED, "status": "RESEARCH_REVIEW_ONLY", "candidates": output,
            "weights_calibrated": False,
            "note": "Synthetic research inputs only; no authenticated prices, earnings or liquidity."}
