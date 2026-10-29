"""Research-only evidence gate for swing candidates.

No fabricated probabilities, targets or automatic orders. Unknown evidence blocks.
"""
import math

REQUIRED = ("independent_validation", "data_quality_pass", "cost_model_pass",
            "portfolio_capacity_pass", "event_risk_reviewed",
            "capital_duration_reviewed", "mae_reviewed")

def assess(candidate):
    if not isinstance(candidate, dict):
        raise ValueError("INVALID_CANDIDATE")
    symbol = candidate.get("symbol")
    if not isinstance(symbol, str) or not symbol.strip():
        raise ValueError("MISSING_SYMBOL")
    evidence = candidate.get("evidence", {})
    if not isinstance(evidence, dict):
        raise ValueError("INVALID_EVIDENCE")
    failed = [key for key in REQUIRED if evidence.get(key) is not True]
    estimates = {}
    for key in ("expected_net_return_pct", "expected_holding_sessions",
                "historical_mae_p10_pct", "validated_win_probability"):
        value = candidate.get(key)
        if value is not None:
            if not isinstance(value, (int, float)) or isinstance(value, bool) or not math.isfinite(value):
                raise ValueError("INVALID_ESTIMATE_" + key)
            if key == "validated_win_probability" and not 0 <= value <= 1:
                raise ValueError("INVALID_PROBABILITY")
            if key == "expected_holding_sessions" and value <= 0:
                raise ValueError("INVALID_HOLDING_DURATION")
        estimates[key] = value
    if any(value is None for value in estimates.values()):
        failed.append("MISSING_VALIDATED_ESTIMATES")
    return {
        "symbol": symbol.strip(),
        "status": "RESEARCH_REVIEW" if not failed else "INSUFFICIENT_EVIDENCE",
        "trade_ready": False,
        "manual_decision_required": True,
        "automatic_orders": False,
        "missing_or_failed_gates": failed,
        "estimates": estimates,
        "warning": "Research evidence is not a forecast guarantee; no execution recommendation.",
    }
