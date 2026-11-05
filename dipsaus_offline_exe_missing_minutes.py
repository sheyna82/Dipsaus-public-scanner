"""Diagnose missing EXE regular-session minutes without inventing bars.

The upstream 1m feed may omit no-trade minutes. Missing intervals remain
unknown; no forward-fill, interpolation or fabricated OHLC is permitted.
"""
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

NY = ZoneInfo("America/New_York")


def audit_regular_session_timestamps(timestamps, session):
    try:
        day = datetime.strptime(session, "%Y-%m-%d").date()
        start = datetime(day.year, day.month, day.day, 9, 30, tzinfo=NY)
        expected = [(start + timedelta(minutes=i)).astimezone(timezone.utc)
                    for i in range(390)]
        observed = []
        for stamp in timestamps:
            ts = datetime.fromtimestamp(stamp, timezone.utc)
            if ts.astimezone(NY).date() == day and 9*60+30 <= ts.astimezone(NY).hour*60+ts.astimezone(NY).minute < 16*60:
                observed.append(ts)
        present = set(observed)
        missing = [ts.astimezone(NY).isoformat() for ts in expected if ts not in present]
        duplicates = len(observed)-len(present)
        off_grid = sum(ts.second != 0 or ts.microsecond != 0 for ts in observed)
        return {"status": "COMPLETE" if not missing and not duplicates and not off_grid else "INCOMPLETE",
                "session": session, "expected_minutes": 390,
                "observed_bars": len(observed), "missing_count": len(missing),
                "missing_minutes_ny": missing[:25],
                "duplicate_count": duplicates, "off_grid_count": off_grid,
                "synthetic_bars_created": 0, "trade_ready": False}
    except (ValueError, TypeError, OverflowError, OSError):
        return {"status": "DATA_BLOCKED", "reason": "invalid_timestamps", "trade_ready": False}
