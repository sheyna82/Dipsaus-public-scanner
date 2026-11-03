"""Research-only adapter for the EXISTING US Yahoo chart row format.

Does not fetch, persist, certify or send alerts. It deliberately reuses the
existing us_momentum_recovery_discovery.chart() output schema (ts/low/close).
"""
from datetime import datetime, timezone
from research.us_setup_intraday_data_preflight import audit_intraday_bars


def adapt_us_chart_rows(rows, *, expected_interval_minutes=5):
    if expected_interval_minutes not in (1, 2, 5, 15, 30, 60):
        raise ValueError("UNSUPPORTED_INTRADAY_INTERVAL")
    converted = []
    for row in rows:
        if not isinstance(row, dict) or row.get("ts") is None:
            return {"usable": False, "reason": "MISSING_SOURCE_TIMESTAMP"}
        try:
            timestamp = datetime.fromtimestamp(row["ts"], timezone.utc).isoformat()
        except (ValueError, TypeError, OverflowError, OSError):
            return {"usable": False, "reason": "INVALID_SOURCE_TIMESTAMP"}
        converted.append({"timestamp": timestamp, "low": row.get("low"), "close": row.get("close")})
    audit = audit_intraday_bars(converted)
    if not audit["usable"]:
        return audit
    times = [datetime.fromisoformat(row["timestamp"]) for row in audit["bars"]]
    gaps = [(b - a).total_seconds() / 60 for a, b in zip(times, times[1:])]
    # Require evidence of the declared granularity. Do not silently accept
    # daily/15-minute data as 5-minute history.
    same_interval = sum(abs(g - expected_interval_minutes) < 0.01 for g in gaps)
    if same_interval < max(3, len(gaps) // 2):
        return {"usable": False, "reason": "INTERVAL_NOT_VERIFIED",
                "matching_steps": same_interval, "total_steps": len(gaps)}
    audit["source_schema"] = "us_momentum_recovery_discovery.chart"
    audit["interval_minutes"] = expected_interval_minutes
    audit["interval_verified_from_timestamps"] = True
    return audit
