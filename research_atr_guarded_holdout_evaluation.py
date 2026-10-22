"""Offline ATR paired evaluation guarded by chronological session embargo.

This orchestration does not certify independent provenance or authorize trading.
"""
from research_atr_chronological_split_gate import audit_chronological_split
from research_atr_incremental_holdout_scoring import fit, predict, evaluate


def evaluate_guarded(training, holdout, sessions, *, embargo_sessions=10):
    gate = audit_chronological_split(training, holdout, sessions,
                                     embargo_sessions=embargo_sessions)
    if gate["status"] != "STRUCTURAL_REVIEW_ONLY":
        return {"status": "DATA_BLOCKED", "gate": gate,
                "independent_holdout_verified": False, "trade_ready": False}
    scores = evaluate(predict(fit(training), holdout))
    return {"status": "DESCRIPTIVE_ONLY", "gate": gate, "scores": scores,
            "independent_holdout_verified": False, "trade_ready": False}
