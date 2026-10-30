"""Offline adapter: hypothesis factor scores into the existing swing pipeline.

Requires fully timestamped provenance for every candidate. Does not source
prices or attest source authenticity; no live scanner or trading integration.
Separate lanes are evaluated separately because their scores are uncalibrated.
"""
from research_swing_hypothesis_score import score_candidate
from research_swing_pipeline import evaluate_research_batch


def evaluate_hypothesis_lane(candidates, *, lane, entry_day, outcome_day,
                             **pipeline_options):
    if not isinstance(candidates, (list, tuple)) or not candidates:
        raise ValueError("empty_hypothesis_cohort")
    prepared = []
    for item in candidates:
        if not isinstance(item, dict):
            raise ValueError("invalid_candidate")
        if item.get("lane") != lane:
            raise ValueError("mixed_uncalibrated_lanes")
        result = score_candidate(lane, item["factors"])
        record = dict(item)
        record["score"] = result["score"]
        provenance = dict(item.get("provenance") or {})
        # Do not rewrite claimed provenance to force it to match the score.
        if str(provenance.get("score")) != result["score"]:
            raise ValueError("score_not_previously_recorded")
        record["provenance"] = provenance
        prepared.append(record)
    if pipeline_options.get("require_provenance") is False:
        raise ValueError("provenance_cannot_be_disabled")
    output = evaluate_research_batch(
        prepared, entry_day=entry_day, outcome_day=outcome_day,
        require_provenance=True, **pipeline_options)
    return {"research_only": True, "lane": lane,
            "score_recipe": "swing_hypothesis_v0_unvalidated",
            "predictive_edge_proven": False,
            "analysis": output}
