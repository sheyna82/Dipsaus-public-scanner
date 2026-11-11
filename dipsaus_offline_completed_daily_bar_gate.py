"""Research-only daily-bar completeness guard.

A bar dated today in the exchange timezone is never accepted as a completed
daily bar. This deliberately conservative guard does not independently verify
the exchange calendar or an exchange's official close.
"""
from datetime import datetime
from zoneinfo import ZoneInfo

EXCHANGE_TZ = ZoneInfo("America/New_York")


def completed_daily_bars(rows, *, now_utc):
    if not isinstance(now_utc, datetime) or now_utc.tzinfo is None:
        return {"status": "DATA_BLOCKED", "reason": "missing_aware_clock"}
    if not isinstance(rows, list) or not rows:
        return {"status": "DATA_BLOCKED", "reason": "missing_bars"}
    today_exchange = now_utc.astimezone(EXCHANGE_TZ).date().isoformat()
    completed = [row for row in rows if isinstance(row, dict)
                 and isinstance(row.get("date"), str) and row["date"] < today_exchange]
    if not completed:
        return {"status": "DATA_BLOCKED", "reason": "no_prior_exchange_day"}
    if any(not isinstance(row, dict) or not isinstance(row.get("date"), str)
           or row["date"] >= today_exchange for row in completed):
        return {"status": "DATA_BLOCKED", "reason": "invalid_completed_rows"}
    return {"status": "PRIOR_DATE_ONLY", "rows": completed,
            "latest_completed_date": completed[-1]["date"],
            "discarded_unconfirmed_bars": len(rows) - len(completed),
            "exchange_calendar_verified": False, "trade_ready": False}
