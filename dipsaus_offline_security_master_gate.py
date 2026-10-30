"""Point-in-time security identity and membership audit (research only).

Requires stable security IDs to avoid treating ticker changes or ticker reuse
as evidence that an issuer disappeared or survived. No external inventory is
implied by a passing structural check.
"""
from datetime import date


def _date(s):
    try:
        return date.fromisoformat(s) if isinstance(s, str) else None
    except ValueError:
        return None


def audit_security_master(records, *, sample_date, independent_inventory_verified=False):
    sample = _date(sample_date)
    if sample is None or not isinstance(records, (list, tuple)) or not records:
        return {"status": "DATA_BLOCKED", "reason": "invalid_input", "trade_ready": False}
    seen_ids = set()
    symbols = {}
    active, inactive = 0, 0
    for row in records:
        if not isinstance(row, dict):
            return {"status": "DATA_BLOCKED", "reason": "invalid_record", "trade_ready": False}
        sid, ticker = row.get("security_id"), row.get("ticker")
        start, end = _date(row.get("listed_from")), _date(row.get("listed_through"))
        if not isinstance(sid, str) or not sid.strip() or not isinstance(ticker, str) or not ticker.strip() or start is None or (row.get("listed_through") is not None and end is None) or (end is not None and end < start):
            return {"status": "DATA_BLOCKED", "reason": "invalid_security_identity_or_dates", "trade_ready": False}
        if sid in seen_ids:
            return {"status": "DATA_BLOCKED", "reason": "duplicate_security_id", "trade_ready": False}
        seen_ids.add(sid)
        is_active = start <= sample and (end is None or sample <= end)
        if is_active:
            active += 1
            symbols.setdefault(ticker, []).append(sid)
        else:
            inactive += 1
    collisions = {ticker: sorted(ids) for ticker, ids in symbols.items() if len(ids) > 1}
    return {"status": "DATA_BLOCKED" if collisions or not independent_inventory_verified else "IDENTITY_REVIEW_REQUIRED",
            "reason": "ticker_collision" if collisions else ("inventory_unverified" if not independent_inventory_verified else None),
            "active_at_sample": active, "inactive_at_sample": inactive,
            "active_ticker_collisions": collisions,
            "survivorship_bias_ruled_out": False,
            "corporate_actions_verified": False,
            "trade_ready": False}
