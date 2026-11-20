"""Research-only candidate ordering: explicit inputs, never a trading authorization.

Weights are provisional heuristics, not calibrated predictive probabilities.
Hard financial thresholds remain separate from ranking.
"""
import math

BLOCKED = {"trade_ready": False, "order_placement_enabled": False,
           "source_authenticity_independently_verified": False}

def rank_research_candidates(candidates):
    if not isinstance(candidates, list):
        return {"status": "RANKING_INPUT_BLOCKED", "reason": "NOT_A_LIST", "candidates": []}
    output = []
    seen = set()
    for item in candidates:
        if not isinstance(item, dict) or not isinstance(item.get("id"), str) or not item["id"].strip():
            return {"status": "RANKING_INPUT_BLOCKED", "reason": "INVALID_ID", "candidates": []}
        if item["id"] in seen:
            return {"status": "RANKING_INPUT_BLOCKED", "reason": "DUPLICATE_ID", "candidates": []}
        seen.add(item["id"])
        values = [item.get(k) for k in ("net_profit_eur", "net_rr", "relative_volume", "market_context", "sector_context")]
        if any(type(v) not in (int, float) or not math.isfinite(v) for v in values):
            output.append({**BLOCKED, "id": item["id"], "status": "UNRANKED_MISSING_OR_INVALID_DATA",
                           "quality_score": None})
            continue
        profit, rr, rvol, market, sector = values
        if not (0 <= market <= 1 and 0 <= sector <= 1 and rvol >= 0):
            output.append({**BLOCKED, "id": item["id"], "status": "UNRANKED_INVALID_RANGE",
                           "quality_score": None})
            continue
        if profit < 150 or rr < 2:
            output.append({**BLOCKED, "id": item["id"], "status": "HARD_FINANCIAL_FILTER_FAILED",
                           "quality_score": None})
            continue
        # The cap prevents a single extreme input from dominating the ordering.
        score = round(30 * min(profit / 300, 1) + 30 * min(rr / 4, 1)
                      + 20 * min(rvol / 2, 1) + 10 * market + 10 * sector, 2)
        output.append({**BLOCKED, "id": item["id"], "status": "PROVISIONAL_RESEARCH_RANK",
                       "quality_score": score, "weights_calibrated": False,
                       "note": "Heuristic ranking only; no liquidity, earnings or source verification."})
    output.sort(key=lambda x: (x["quality_score"] is None,
                                -(x["quality_score"] or 0), x["id"]))
    return {"status": "RESEARCH_RANKING_ONLY", "candidates": output,
            "weights_calibrated": False, "trade_ready": False,
            "order_placement_enabled": False}
