"""Multitimeframe evidence gate: one-minute turns cannot qualify swing trades."""
from datetime import datetime, timezone
from research.us_level_evidence_20261117 import fresh

def assess_trend(timeframes, now=None):
    checks = {}
    for tf in ("intraday", "hourly", "daily"):
        item = timeframes.get(tf) if isinstance(timeframes, dict) else None
        if not isinstance(item, dict) or not fresh(item.get("checked_utc"), now, 900):
            checks[tf] = "UNKNOWN"
        elif item.get("source") and item.get("verified") is True and item.get("higher_low") is True and item.get("reclaim") is True:
            checks[tf] = "PASS"
        elif item.get("verified") is True and (item.get("higher_low") is False or item.get("reclaim") is False):
            checks[tf] = "BLOCK"
        else:
            checks[tf] = "UNKNOWN"
    status = "BLOCK" if "BLOCK" in checks.values() else "MULTITIMEFRAME_CONFIRMED" if all(v == "PASS" for v in checks.values()) else "INCOMPLETE"
    return {"status": status, "checks": checks, "trade_ready": False}
