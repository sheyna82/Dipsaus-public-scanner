"""Conservative, shadow-only bridge from verified PRE-ALERT observations.

Never fabricates PASS, order readiness or phone notification clearance.
Other unified gates stay UNKNOWN until independently sourced.
"""
from datetime import datetime, timezone


def _stamp(value, now, max_age=900):
    if not isinstance(value, str):
        return None
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            return None
        age = (now - dt).total_seconds()
        return dt if -30 <= age <= max_age else None
    except (ValueError, OverflowError, TypeError):
        return None


def evidence_from_prealert(row, report_generated_utc, now=None):
    """Return CAUTION evidence only for fresh, explicitly observed events."""
    now = now or datetime.now(timezone.utc)
    if not isinstance(row, dict):
        return {}
    if not _stamp(report_generated_utc, now):
        return {}
    quote = _stamp(row.get("provider_quote_utc"), now)
    if quote is None or row.get("provider_freshness_pass") is not True:
        return {}
    if not isinstance(row.get("symbol"), str) or not row["symbol"]:
        return {}
    evidence = {}
    if row.get("prealert_trigger_observed") is True:
        evidence["early_recovery"] = {
            "status": "CAUTION", "checked_utc": quote.isoformat(),
            "source": "PREALERT_FRESH_PROVIDER_TRIGGER",
        }
    ratio = row.get("recent_volume_ratio")
    if (row.get("prealert_trigger_observed") is True
            and isinstance(ratio, (int, float)) and not isinstance(ratio, bool)
            and 1.5 <= ratio < float("inf")):
        evidence["volume_confirmation"] = {
            "status": "CAUTION", "checked_utc": quote.isoformat(),
            "source": "PREALERT_RECENT_VOLUME_RATIO",
        }
    return evidence
