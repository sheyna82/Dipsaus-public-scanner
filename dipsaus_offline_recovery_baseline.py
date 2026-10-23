"""Offline recovery candidate baseline; no learned probabilities or live orders.

All inputs must be caller-attested, point-in-time features. This is a
transparent *ranking baseline*, not a calibrated forecast.
"""
import math


def score_recovery_candidate(features):
    """Return a conservative research-only score or an abstention."""
    required = ("relative_strength_20d", "return_5d", "volume_ratio_20d",
                "atr_pct", "market_return_5d", "days_to_earnings")
    if not isinstance(features, dict):
        return None
    for key in required:
        value = features.get(key)
        if type(value) not in (int, float) or not math.isfinite(value):
            return {"decision": "ABSTAIN", "reason": "missing_or_invalid_feature",
                    "research_only": True, "trade_ready": False,
                    "order_instruction": None}
    rs, ret, vol, atr, market, earnings = (features[k] for k in required)
    if vol <= 0 or atr <= 0 or atr > 100 or earnings < 0 or int(earnings) != earnings:
        return {"decision": "ABSTAIN", "reason": "invalid_feature_range",
                "research_only": True, "trade_ready": False,
                "order_instruction": None}
    if earnings <= 3:
        return {"decision": "ABSTAIN", "reason": "imminent_earnings",
                "research_only": True, "trade_ready": False,
                "order_instruction": None}
    points = {
        "relative_strength": 2 if rs >= 2 else (1 if rs >= 0 else 0),
        "recent_recovery": 2 if 0 < ret <= 8 else (1 if -3 <= ret <= 0 else 0),
        "volume_confirmation": 1 if 1.1 <= vol <= 3 else 0,
        "controlled_volatility": 1 if atr <= 5 else 0,
        "market_context": 1 if market >= -2 else 0,
    }
    total = sum(points.values())
    return {"decision": "RESEARCH_CANDIDATE" if total >= 5 else "NO_CANDIDATE",
            "score": total, "max_score": 7, "components": points,
            "horizon": "unvalidated", "probability": None,
            "research_only": True, "trade_ready": False,
            "order_instruction": None,
            "limitations": "Heuristic baseline; no historical fit, calibration or fill model."}
