"""Research-only whole-scanner readiness audit; no trading decisions.

Checks distinct system dimensions independently rather than optimizing a
single symbol. Explicit evidence is required; missing proof remains unknown.
"""
DIMENSIONS = (
    "marketwide_universe_coverage",
    "point_in_time_data_integrity",
    "multi_sector_chronological_holdout",
    "recovery_entry_quality",
    "downside_and_false_alert_rates",
    "profit_protection_validation",
    "notification_delivery_reliability",
    "latency_and_runtime_budget",
    "live_research_separation",
)


def audit_system(evidence):
    if not isinstance(evidence, dict):
        return {"status": "DATA_BLOCKED", "reason": "invalid_evidence", "trade_ready": False}
    checks = {}
    for name in DIMENSIONS:
        item = evidence.get(name)
        if not isinstance(item, dict):
            checks[name] = {"status": "UNKNOWN", "reason": "MISSING_EVIDENCE"}
            continue
        status = item.get("status")
        source = item.get("source")
        if status not in ("PASS", "FAIL") or not isinstance(source, str) or not source.strip():
            checks[name] = {"status": "UNKNOWN", "reason": "UNVERIFIED_EVIDENCE"}
        else:
            checks[name] = {"status": status, "source": source}
    failed = [k for k, v in checks.items() if v["status"] == "FAIL"]
    unknown = [k for k, v in checks.items() if v["status"] == "UNKNOWN"]
    return {"status": "RESEARCH_BLOCKED" if failed else
                      "RESEARCH_INCOMPLETE" if unknown else "REVIEW_REQUIRED",
            "dimensions": checks, "failed": failed, "unknown": unknown,
            "verified_passes": sum(v["status"] == "PASS" for v in checks.values()),
            "total_dimensions": len(DIMENSIONS),
            "trade_ready": False, "notify": False, "automatic_orders": False}
