"""Research-only orchestration: structural gates before descriptive ATR scoring.

No external source verification, trade execution, or live notifications.
"""
from research_walk_forward_split_gate import validate_walk_forward_split
from research_atr_incremental_holdout_scoring import fit, predict, evaluate
from research_point_in_time_availability_gate import assess_point_in_time_record
from research_walk_forward_split_gate import _timestamp


def evaluate_gated_atr_holdout(training, holdout, *, evaluation_at, embargo_seconds=0):
    """Require chronological label availability before fitting and scoring.

    The structural gate cannot establish independent data provenance.
    Results therefore remain descriptive and never trade-ready.
    """
    evaluation_time = _timestamp(evaluation_at)
    audit = validate_walk_forward_split(
        training, holdout, embargo_seconds=embargo_seconds)
    for row in (*training, *holdout):
        point_in_time = assess_point_in_time_record(
            row, decision_at=row["event_at"])
        if not point_in_time["accepted"]:
            raise ValueError("point_in_time_rejected:" + ",".join(point_in_time["reasons"]))
    if any(_timestamp(row["label_available_at"]) > evaluation_time
           for row in holdout):
        raise ValueError("holdout_labels_not_yet_available")
    training_features = [
        {key: row[key] for key in (
            "structure_above_20d_mean", "market_20d_positive",
            "atr_expanding", "severe")}
        for row in training
    ]
    holdout_features = [
        {key: row[key] for key in (
            "structure_above_20d_mean", "market_20d_positive",
            "atr_expanding", "severe")}
        for row in holdout
    ]
    model = fit(training_features)
    result = evaluate(predict(model, holdout_features))
    return {
        **result,
        "structural_split_accepted": audit["accepted"],
        "independent_source_verified": False,
        "independent_holdout_verified": False,
        "trade_ready": False,
        "descriptive_only": True,
    }
