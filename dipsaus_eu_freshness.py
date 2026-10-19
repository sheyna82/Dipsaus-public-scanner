"""Private EU report freshness classification; never relaxes the alert gate."""
from datetime import datetime, timezone, timedelta

def classify_eu_report(report, now=None, max_age_minutes=25):
    now = now or datetime.now(timezone.utc)
    if not isinstance(report, dict) or not isinstance(report.get("generated_utc"), str):
        return {"fresh": False, "reason": "MISSING_OR_INVALID_REPORT"}
    try:
        stamp = datetime.fromisoformat(report["generated_utc"].replace("Z", "+00:00"))
        if stamp.tzinfo is None:
            return {"fresh": False, "reason": "INVALID_TIMESTAMP"}
        age = (now-stamp).total_seconds()
        if age < 0:
            return {"fresh": False, "reason": "FUTURE_TIMESTAMP"}
        if age > max_age_minutes*60:
            return {"fresh": False, "reason": "EXPIRED_REPORT"}
        return {"fresh": True, "reason": "FRESH"}
    except (ValueError, TypeError, OverflowError):
        return {"fresh": False, "reason": "MISSING_OR_INVALID_REPORT"}
