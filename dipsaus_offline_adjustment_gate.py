"""Fail-closed data quality gate for cross-provider research comparisons.

Price-adjustment compatibility must be independently established before
a comparison may be described as validated. No trading or live alerts.
"""


def assess_cross_provider_comparison(audit):
    if not isinstance(audit, dict):
        return {"status": "BLOCKED", "reason": "missing_audit", "trade_ready": False}
    if audit.get("raw_ohlc_cross_provider_comparison_caution") is True:
        return {"status": "BLOCKED", "reason": "unresolved_adjustment_mismatch",
                "trade_ready": False}
    if audit.get("adjustment_compatibility_verified") is not True:
        return {"status": "BLOCKED", "reason": "adjustment_policy_unverified",
                "trade_ready": False}
    if audit.get("historical_earnings_verified") is not True:
        return {"status": "RESEARCH_ONLY", "reason": "earnings_not_verified",
                "trade_ready": False}
    return {"status": "RESEARCH_ONLY", "reason": "additional_validation_required",
            "trade_ready": False}
