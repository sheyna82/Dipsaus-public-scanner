"""Private candidate registry adapter for the read-only coverage audit.

Accepts registry documents supplied by the private runtime; never fetches,
logs, persists or publishes tickers. This is NOT a live scanner integration.
"""
from datetime import datetime, timezone
from candidate_coverage_audit import reconcile

VALID_STATES = frozenset({"REGISTERED", "ACTIVE", "APPROACHING",
                          "VERIFY_NOW", "BUY_CANDIDATE", "DATA_BLOCKED",
                          "STALE", "DEFERRED", "INVALIDATED", "CLOSED"})

def validate_registry(registry):
    if not isinstance(registry, dict) or registry.get("schema_version") != 1:
        raise ValueError("unsupported registry schema")
    entries = registry.get("candidates")
    if not isinstance(entries, list):
        raise ValueError("registry candidates must be a list")
    ids = set()
    for row in entries:
        if not isinstance(row, dict):
            raise ValueError("candidate must be an object")
        cid = row.get("id")
        if not isinstance(cid, str) or not cid.strip() or cid in ids:
            raise ValueError("missing or duplicate candidate id")
        ids.add(cid)
        if row.get("status") not in VALID_STATES:
            raise ValueError("invalid candidate state")
        if not isinstance(row.get("symbol"), str) or not row["symbol"].strip():
            raise ValueError("missing provider symbol")
        if row["status"] in ("CLOSED", "INVALIDATED") and not row.get("closure_reason"):
            raise ValueError("closed candidate requires reason")
    return entries

def audit_private_registry(registry, observations, *, now=None,
                           max_age_seconds=600):
    """Returns private details and safe aggregate; caller controls visibility."""
    entries = validate_registry(registry)
    if not isinstance(observations, list):
        raise ValueError("observations must be a list")
    return reconcile(entries, observations, now=now, max_age_seconds=max_age_seconds)

def public_aggregate(result):
    """Whitelist only nonidentifying counters for public logs."""
    s = result["summary"]
    return {k: s[k] for k in
            ("active", "fresh_checked", "blocked", "deferred", "overdue",
             "reconciled")}
