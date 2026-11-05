"""Research-only proof-of-coverage gate for earnings calendar snapshots.

A source's claimed date range alone cannot prove it captured all known events.
An independent inventory is required for each issuer and time interval.
This is a structural comparison only, not independent verification of either source.
"""


def audit_calendar_coverage(expected_issuer_ids, observed_issuer_ids, *,
                            inventory_asof_verified=False,
                            source_independent=False):
    if not isinstance(expected_issuer_ids, (list, tuple, set)) or not isinstance(observed_issuer_ids, (list, tuple, set)):
        return {"status": "DATA_BLOCKED", "reason": "invalid_inventory", "trade_ready": False}
    if any(not isinstance(x, str) or not x.strip() for x in [*expected_issuer_ids, *observed_issuer_ids]):
        return {"status": "DATA_BLOCKED", "reason": "invalid_issuer_id", "trade_ready": False}
    expected = set(expected_issuer_ids)
    observed = set(observed_issuer_ids)
    if not expected or not inventory_asof_verified or not source_independent:
        return {"status": "DATA_BLOCKED", "reason": "missing_independent_asof_inventory",
                "expected_issuers": len(expected), "trade_ready": False}
    missing = sorted(expected - observed)
    unexpected = sorted(observed - expected)
    return {"status": "COVERAGE_GAP" if missing else "INVENTORY_MATCH",
            "expected_issuers": len(expected), "observed_issuers": len(observed),
            "missing_issuer_ids": missing, "unexpected_issuer_ids": unexpected,
            "independent_event_completeness_verified": False,
            "trade_ready": False}
