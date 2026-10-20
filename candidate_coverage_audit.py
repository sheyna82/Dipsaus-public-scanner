"""Pure, read-only candidate coverage reconciliation.

This module has no network access, no notification side effects and no
dependency on private config layout. Callers provide sanitized records.
Do not print per-symbol results to public GitHub Actions logs.
"""
from collections import Counter
from datetime import datetime, timezone

VALID = frozenset({"FRESH_CHECKED", "DATA_BLOCKED", "DEFERRED"})
CLOSED = frozenset({"CLOSED", "INVALIDATED"})

def _parse_utc(value):
    if not isinstance(value, str):
        return None
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return dt.astimezone(timezone.utc) if dt.tzinfo else None
    except ValueError:
        return None

def reconcile(candidates, observations, *, now=None, max_age_seconds=600):
    """Return private per-candidate detail plus public-safe aggregate counts.

    Candidate ID is immutable and unique. Exactly one latest observation per
    active candidate is required. Absence or expired evidence is OVERDUE,
    never a silent 'no setup'. Market-closed candidates must be DEFERRED with
    an explicit reason; fresh quote checks require timestamps.
    """
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        raise ValueError("now must be timezone aware")
    if max_age_seconds <= 0:
        raise ValueError("max_age_seconds must be positive")
    active = {}
    for candidate in candidates:
        cid = candidate.get("id")
        if not isinstance(cid, str) or not cid:
            raise ValueError("candidate id missing")
        if cid in active:
            raise ValueError("duplicate candidate id")
        if candidate.get("status") not in CLOSED:
            active[cid] = candidate
    seen = {}
    for observation in observations:
        cid = observation.get("candidate_id")
        if cid in seen:
            raise ValueError("duplicate observation for candidate")
        seen[cid] = observation
    details = []
    for cid in sorted(active):
        item = seen.get(cid)
        status = item.get("status") if item else None
        timestamp = _parse_utc(item.get("checked_at")) if item else None
        age = (now - timestamp).total_seconds() if timestamp else None
        valid_age = age is not None and -30 <= age <= max_age_seconds
        valid_reason = status == "FRESH_CHECKED" or bool(item and item.get("reason"))
        covered = status in VALID and valid_age and valid_reason
        details.append({
            "candidate_id": cid,
            "coverage": status if covered else "OVERDUE",
            "reason": item.get("reason") if covered else "MISSING_OR_STALE_EVIDENCE",
            "checked_at": item.get("checked_at") if item else None,
        })
    counts = Counter(row["coverage"] for row in details)
    summary = {
        "active": len(active),
        "fresh_checked": counts["FRESH_CHECKED"],
        "blocked": counts["DATA_BLOCKED"],
        "deferred": counts["DEFERRED"],
        "overdue": counts["OVERDUE"],
    }
    summary["reconciled"] = summary["active"] == (
        summary["fresh_checked"] + summary["blocked"] + summary["deferred"]
    )
    return {"summary": summary, "private_details": details}
