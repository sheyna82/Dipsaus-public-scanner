"""Offline evidence-aware quality ranking for US shadow research only.

A score is a triage priority, never an execution approval. Missing evidence
does not become zero, and partial scores are not comparable as full scores.
"""
from math import isfinite

WEIGHTS = {
    "recovery_structure": 30,
    "reward_resistance": 25,
    "relative_market_sector": 20,
    "rvol_liquidity": 15,
    "news_events": 10,
}
VERSION = "US_QUALITY_V1_PROVISIONAL"

def rank_quality_components(components):
    base = {"version": VERSION, "trade_ready": False, "notify": False,
            "automatic_orders": False, "order_placement_enabled": False,
            "research_only": True}
    if not isinstance(components, dict) or set(components) - set(WEIGHTS):
        return {**base, "status": "INVALID_COMPONENTS", "score_0_100": None,
                "unknown": list(WEIGHTS), "blocks": ["COMPONENT_SCHEMA_INVALID"]}
    unknown, scored, details = [], 0.0, {}
    for key, weight in WEIGHTS.items():
        item = components.get(key)
        if item is None:
            unknown.append(key)
            details[key] = {"status": "UNKNOWN", "weight": weight, "points": None}
            continue
        if (not isinstance(item, dict) or item.get("verified_asof") is not True
                or not isinstance(item.get("fraction"), (float, int))
                or isinstance(item.get("fraction"), bool)
                or not isfinite(item["fraction"]) or not 0 <= item["fraction"] <= 1):
            return {**base, "status": "INVALID_COMPONENTS", "score_0_100": None,
                    "unknown": list(WEIGHTS), "blocks": ["COMPONENT_EVIDENCE_INVALID"]}
        points = round(weight * item["fraction"], 4)
        scored += points
        details[key] = {"status": "EVIDENCE_DECLARED_UNVERIFIED_SOURCE",
                        "weight": weight, "points": points}
    # Caller-declared as-of evidence is not independently authenticated.
    complete = not unknown
    return {**base, "status": "COMPLETE_UNATTESTED" if complete else "PARTIAL_UNRANKED",
            "score_0_100": round(scored, 2) if complete else None,
            "observed_points": round(scored, 2),
            "unknown": unknown, "components": details,
            "blocks": ["SOURCE_ATTESTATION_PENDING", "WEIGHTS_NOT_EMPIRICALLY_VALIDATED"]}

def order_research_queue(candidates):
    """Rank complete candidates first; keep incomplete cases, stable input order."""
    if not isinstance(candidates, list):
        raise ValueError("CANDIDATES_INVALID")
    rows = []
    for i, candidate in enumerate(candidates):
        if not isinstance(candidate, dict) or not isinstance(candidate.get("symbol"), str) or not candidate["symbol"].strip():
            raise ValueError("CANDIDATE_INVALID")
        result = rank_quality_components(candidate.get("quality_components"))
        rows.append({"symbol": candidate["symbol"], "quality": result, "original_index": i})
    rows.sort(key=lambda x: (x["quality"]["score_0_100"] is None,
                             -(x["quality"]["score_0_100"] or 0),
                             x["original_index"]))
    return {"status": "RESEARCH_RANKING_ONLY", "rows": rows,
            "trade_ready": False, "notify": False, "automatic_orders": False,
            "order_placement_enabled": False}
