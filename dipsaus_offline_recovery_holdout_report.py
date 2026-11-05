"""Offline holdout report with explicit selection and exclusion accounting.

Never tune thresholds on holdout results. No learned probabilities or live signals.
"""
from dipsaus_offline_recovery_holdout import chronological_holdout
from dipsaus_offline_recovery_pipeline import evaluate_recovery_research


def evaluate_holdout_recovery(observations, *, holdout_fraction=0.25,
                              embargo_sessions=10, horizon=10,
                              minimum_resolved=20):
    split = chronological_holdout(
        observations, holdout_fraction=holdout_fraction,
        embargo_sessions=embargo_sessions)
    if split is None:
        return None
    development = evaluate_recovery_research(
        split["development"], minimum_resolved=minimum_resolved,
        horizon=horizon)
    holdout = evaluate_recovery_research(
        split["holdout"], minimum_resolved=minimum_resolved,
        horizon=horizon)
    if development is None or holdout is None:
        return None
    return {
        "development": development["score_report"],
        "holdout": holdout["score_report"],
        "development_nominated": development["nominated"],
        "holdout_nominated": holdout["nominated"],
        "development_included": development["included"],
        "holdout_included": holdout["included"],
        "development_excluded": development["excluded"],
        "holdout_excluded": holdout["excluded"],
        "purged_count": len(split["purged_ids"]),
        "holdout_start": split["holdout_start"],
        "research_only": True, "trade_ready": False,
        "historical_performance_validated": False,
        "warning": "Holdout is not independent if researchers retune after seeing it; no verified historical data or execution costs."
    }
