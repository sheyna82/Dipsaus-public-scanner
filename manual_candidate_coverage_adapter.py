"""Read-only adapter: existing manual candidate config -> private audit registry.

No side effects. Does not persist symbols or emit them in public logs.
This adapter does NOT enable alerts or modify existing scanner routes.
"""
from datetime import datetime, timezone
from private_candidate_registry import audit_private_registry, public_aggregate

def from_manual_configs(primary, supplemental=None):
    """Return schema-v1 registry with stable IDs for explicit manual candidates.

    Supplemental candidates override primary settings as the current scanner
    does, but retain a stable provider-symbol identity. If neither config has
    an entry it cannot be assumed to be monitored.
    """
    if not isinstance(primary, dict):
        raise ValueError("primary config missing")
    if supplemental is None:
        supplemental = {}
    if not isinstance(supplemental, dict):
        raise ValueError("supplemental config invalid")
    combined = {}
    for cfg in (primary, supplemental):
        candidates = cfg.get("candidates", {})
        if not isinstance(candidates, dict):
            raise ValueError("candidates mapping invalid")
        combined.update(candidates)
    rows = []
    for symbol, info in sorted(combined.items()):
        if not isinstance(symbol, str) or not symbol or not isinstance(info, dict):
            raise ValueError("invalid manual candidate")
        rows.append({
            "id": "manual:" + symbol,
            "symbol": symbol,
            "status": "ACTIVE",
            "origin": "MANUAL",
            "monitor_mode": info.get("monitor_mode"),
            "broker_listing": info.get("broker_listing"),
            "currency": info.get("currency"),
        })
    return {"schema_version": 1, "candidates": rows}

def from_manual_report(report, *, checked_at):
    """Convert existing per-symbol report rows into coverage observations.

    Crucially a research-only WATCH is still a checked candidate, not an
    actionable buy. A DATA-BLOCKED row is a checked attempt but not fresh.
    Missing freshness must never count as FRESH_CHECKED.
    """
    if not isinstance(report, dict) or not isinstance(report.get("rows"), list):
        raise ValueError("invalid manual report")
    out = []
    seen = set()
    for row in report["rows"]:
        if not isinstance(row, dict):
            raise ValueError("invalid manual report row")
        symbol = row.get("symbol")
        if not isinstance(symbol, str) or not symbol:
            continue
        # Existing report also contains portfolio and US-auto rows; exclude.
        if row.get("watch_type"):
            continue
        cid = "manual:" + symbol
        if cid in seen:
            raise ValueError("duplicate manual report symbol")
        seen.add(cid)
        if row.get("status") == "DATA-BLOCKED" or not row.get("provider_freshness_pass"):
            status = "DATA_BLOCKED"
            reason = "PROVIDER_QUOTE_NOT_FRESH" if row.get("status") != "DATA-BLOCKED" else "DATA_BLOCKED"
        else:
            status = "FRESH_CHECKED"
            reason = None
        out.append({"candidate_id": cid, "status": status,
                    "checked_at": checked_at, "reason": reason})
    return out

def audit_manual_candidate_coverage(primary, supplemental, report, *,
                                    checked_at, now=None, max_age_seconds=600):
    """Private result; public logs may receive public_aggregate(result) only."""
    registry = from_manual_configs(primary, supplemental)
    # Trust the report generation time, never a caller-supplied fresh timestamp.
    generated = report.get("generated_utc") if isinstance(report, dict) else None
    if generated is None:
        raise ValueError("report generation timestamp missing")
    observations = from_manual_report(report, checked_at=generated)
    result = audit_private_registry(registry, observations, now=now,
                                    max_age_seconds=max_age_seconds)
    return result
