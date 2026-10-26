"""Descriptive stage hypotheses, not predictions or buy/sell signals.

The rules deliberately separate momentum continuation from early reversal.
They must be validated out-of-sample against net returns before use.
"""
def classify_stage(metrics):
    if metrics.get("status")!="historical_context_available":
        return {"stage":"UNCLASSIFIED","reason":"insufficient_validated_context","research_only":True}
    m5=metrics["return_5_sessions_pct"]
    m20=metrics["return_20_sessions_pct"]
    gap=metrics["distance_below_20_session_high_pct"]
    recovery=metrics["recovery_from_20_session_low_pct"]
    if m20>=5 and gap<=2:
        stage="MOMENTUM_NEAR_HIGH"
        reason="strong_20_session_momentum_near_recent_high"
    elif m20<=-3 and m5>0 and gap>=4:
        stage="POSSIBLE_EARLY_REVERSAL"
        reason="negative_20_session_momentum_with_positive_5_session_turn"
    elif m20<=-3 and m5<=0:
        stage="DOWNTREND_NOT_YET_CONFIRMED"
        reason="negative_5_and_20_session_momentum"
    elif m20>0 and m5<0:
        stage="PULLBACK_AFTER_RISE"
        reason="short_pullback_in_positive_20_session_trend"
    else:
        stage="MIXED_CONTEXT"
        reason="no_clear_stage_from_simple_daily_features"
    return {"stage":stage,"reason":reason,"research_only":True,
            "trade_ready":False,"predictive_edge_verified":False,
            "recovery_from_20_session_low_pct":recovery}
