"""Minimal Spoor 3 research top-three view over existing candidate review data.

No market fetch, no live scanner integration, no orders. Scores are heuristic.
"""
from research_candidate_review import review_research_candidates

BLOCKED = {"trade_ready": False, "order_placement_enabled": False}

def top_three_research_setups(candidates):
    """Return at most three eligible setups; preserve excluded candidates separately."""
    reviewed = review_research_candidates(candidates)
    if reviewed["status"] != "RESEARCH_REVIEW_ONLY":
        return {**BLOCKED, "status": "TOP3_INPUT_BLOCKED",
                "reason": reviewed.get("reason"), "top3": [], "excluded": []}
    eligible = []
    excluded = []
    for item in reviewed["candidates"]:
        summary = {"id": item["id"], "quality_score": item["quality_score"],
                   "research_disposition": item["research_disposition"],
                   "trade_ready": False, "order_placement_enabled": False}
        if item["eligible_for_further_research"] and item["quality_score"] is not None:
            eligible.append(summary)
        else:
            excluded.append(summary)
    return {**BLOCKED, "status": "TOP3_RESEARCH_ONLY",
            "top3": eligible[:3], "eligible_count": len(eligible),
            "excluded": excluded, "weights_calibrated": False,
            "note": "Uses supplied research data only; not a live signal or trade recommendation."}
