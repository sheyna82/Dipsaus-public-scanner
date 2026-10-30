"""Research-only inventory of historical-universe inclusion and exclusions.

Purpose: detect survivorship bias and unsupported point-in-time membership
before evaluating the frozen full-score strategy. This is a metadata audit,
not a substitute for a vendor's complete security master.
"""


def audit_universe_coverage(records, *, expected_total=None):
    if not isinstance(records, (list, tuple)) or not records:
        return {"status": "DATA_BLOCKED", "reason": "empty_or_invalid_universe",
                "trade_ready": False}
    if expected_total is not None and (type(expected_total) is not int or expected_total < len(records)):
        return {"status": "DATA_BLOCKED", "reason": "invalid_expected_total",
                "trade_ready": False}
    seen = set()
    counts = {"active": 0, "delisted": 0, "unknown": 0}
    exclusions = {}
    sectors = {}
    for record in records:
        if not isinstance(record, dict):
            return {"status": "DATA_BLOCKED", "reason": "invalid_record", "trade_ready": False}
        symbol = record.get("symbol")
        if not isinstance(symbol, str) or not symbol.strip() or symbol in seen:
            return {"status": "DATA_BLOCKED", "reason": "duplicate_or_missing_symbol",
                    "trade_ready": False}
        seen.add(symbol)
        status = record.get("listing_status", "unknown")
        if status not in counts:
            return {"status": "DATA_BLOCKED", "reason": "invalid_listing_status",
                    "trade_ready": False}
        counts[status] += 1
        sector = record.get("sector_at_sample_date")
        if isinstance(sector, str) and sector.strip():
            sectors[sector] = sectors.get(sector, 0) + 1
        reason = record.get("exclusion_reason")
        if reason is not None:
            if not isinstance(reason, str) or not reason.strip():
                return {"status": "DATA_BLOCKED", "reason": "invalid_exclusion_reason",
                        "trade_ready": False}
            exclusions[reason] = exclusions.get(reason, 0) + 1
    missing = None if expected_total is None else expected_total - len(records)
    return {
        "status": "COVERAGE_REVIEW_REQUIRED",
        "records": len(records),
        "expected_total": expected_total,
        "unaccounted_securities": missing,
        "listing_status_counts": counts,
        "sector_at_sample_date_counts": sectors,
        "exclusion_reason_counts": exclusions,
        "all_membership_dates_verified": False,
        "delisted_coverage_independently_verified": False,
        "survivorship_bias_ruled_out": False,
        "trade_ready": False,
    }
