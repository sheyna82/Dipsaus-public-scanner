"""Offline chronological baseline-versus-ATR experiment.

This is an integration harness, not a claim of independent historical
validation. No data downloads, model selection, or production signals.
"""
from datetime import datetime, time, timezone
from research_daily_feature_label_join import join_features_and_labels
from research_benchmark_market_trend import attach_market_trend, eligible_model_rows
from research_walk_forward_split_gate import validate_walk_forward_split
from research_atr_incremental_holdout_scoring import fit, predict, evaluate


def _timestamp(day):
    return datetime.combine(datetime.strptime(day, "%Y-%m-%d").date(),
                            time(23, 59), tzinfo=timezone.utc).isoformat()


def evaluate_chronological_csv(stock_payload, benchmark_payload, *,
                               split_date, horizon=10, threshold=0.08,
                               embargo_seconds=0, holdout_end_date=None):
    """Use training labels known by first holdout event; refuse invalid splits.

    Split is predetermined by caller, not chosen from holdout results.
    The market benchmark must be independently sourced and date-aligned.
    """
    if not isinstance(split_date, str):
        raise ValueError("invalid_split_date")
    datetime.strptime(split_date, "%Y-%m-%d")
    if holdout_end_date is not None:
        if not isinstance(holdout_end_date, str):
            raise ValueError("invalid_holdout_end_date")
        datetime.strptime(holdout_end_date, "%Y-%m-%d")
        if holdout_end_date <= split_date:
            raise ValueError("holdout_end_must_follow_split")
    joined = join_features_and_labels(stock_payload, horizon=horizon,
                                      threshold=threshold)
    aligned = eligible_model_rows(attach_market_trend(joined, benchmark_payload))
    training = [r for r in aligned if r["date"] < split_date
                and r["label_available_date"] < split_date]
    holdout = [r for r in aligned if r["date"] >= split_date
               and (holdout_end_date is None or r["date"] < holdout_end_date)]
    train_gate = [{"event_at": _timestamp(r["date"]),
                   "label_available_at": _timestamp(r["label_available_date"])}
                  for r in training]
    holdout_gate = [{"event_at": _timestamp(r["date"]),
                     "label_available_at": _timestamp(r["label_available_date"])}
                    for r in holdout]
    gate = validate_walk_forward_split(train_gate, holdout_gate,
                                       embargo_seconds=embargo_seconds)
    model = fit(training)
    metrics = evaluate(predict(model, holdout))
    return {**metrics, "split_date": split_date,
            "holdout_end_date": holdout_end_date,
            "training_events": gate["training_events"],
            "holdout_events": gate["holdout_events"],
            "independent_holdout_verified": False,
            "point_in_time_verified": False,
            "trade_ready": False}
