"""Fail-closed readiness gate for preregistered multi-ticker DIPSAUS score study.

Separates the price-only event experiment from the full score>=5 strategy.
An availability declaration is NOT independent verification of data provenance.
No market access, alerting, trade recommendations or parameter fitting.
"""

REQUIRED = (
    "point_in_time_earnings_calendar",
    "adjusted_ohlcv_corporate_actions",
    "delisted_stock_coverage",
    "historical_sector_membership",
    "benchmark_compatible_history",
    "chronological_holdout_embargo",
    "same_date_selected_skipped_comparators",
    "provider_license_and_provenance",
)


def assess_multiticker_readiness(evidence):
    if not isinstance(evidence, dict):
        return {"status": "DATA_BLOCKED", "reason": "invalid_evidence",
                "trade_ready": False, "predictive_edge_proven": False}
    missing = [key for key in REQUIRED if evidence.get(key) is not True]
    unknown = sorted(set(evidence) - set(REQUIRED))
    return {
        "status": "DATA_BLOCKED" if missing else "READY_FOR_INDEPENDENT_AUDIT",
        "missing_or_unverified": missing,
        "unrecognized_fields": unknown,
        "requirements_checked": len(REQUIRED),
        "score_strategy": "frozen_score_at_least_5",
        "price_only_four_event_rule_is_not_equivalent": True,
        "independent_data_audit_completed": False,
        "independent_holdout_test_completed": False,
        "predictive_edge_proven": False,
        "trade_ready": False,
    }


if __name__ == "__main__":
    import json
    print(json.dumps(assess_multiticker_readiness({}), sort_keys=True))
