"""Whole-scanner aggregate notification-funnel integrity checks.

Only aggregate counters are accepted. This is a structural audit, not proof
that a phone received a push or that a missed alert should have been sent.
"""
STAGES = ("examined", "eligible", "attempted", "accepted_by_provider", "device_confirmed")


def audit_funnel(counters):
    if not isinstance(counters, dict):
        return {"status": "DATA_BLOCKED", "reason": "INVALID_COUNTERS", "trade_ready": False}
    checks = {}
    for market in ("EU", "US"):
        row = counters.get(market)
        if not isinstance(row, dict):
            checks[market] = {"status": "UNKNOWN", "reason": "MISSING_MARKET"}
            continue
        if any(type(row.get(k)) is not int or row[k] < 0 for k in STAGES):
            checks[market] = {"status": "UNKNOWN", "reason": "MISSING_OR_INVALID_STAGE"}
            continue
        counts = [row[k] for k in STAGES]
        if any(a < b for a, b in zip(counts, counts[1:])):
            checks[market] = {"status": "INCONSISTENT", "reason": "STAGE_COUNT_INCREASE"}
            continue
        checks[market] = {
            "status": "COUNTS_CONSISTENT",
            "counts": {k: row[k] for k in STAGES},
            "not_eligible": counts[0] - counts[1],
            "eligible_not_attempted": counts[1] - counts[2],
            "attempted_not_provider_accepted": counts[2] - counts[3],
            "provider_accepted_not_device_confirmed": counts[3] - counts[4],
            "device_delivery_verified": counts[4] > 0,
        }
    return {"status": "DATA_BLOCKED" if any(x["status"] == "INCONSISTENT"
                                             for x in checks.values()) else
                      "INCOMPLETE" if any(x["status"] == "UNKNOWN"
                                          for x in checks.values()) else "DESCRIPTIVE_ONLY",
            "markets": checks, "notification_delivery_proven": False,
            "trade_ready": False, "notify": False}
