"""Research-only daily-session freshness policy with explicit market-local date.

No wall clock, timezone guess, provider verification, or live alerting.
"""
from datetime import date


def check_daily_session(observed_session, expected_completed_session,
                        *, provider_verified=False):
    """Fail closed unless the supplied last *completed* session matches exactly.

    Caller must independently establish US exchange holiday/session calendar
    and ensure the bar is final, not an intraday partial daily bar.
    """
    try:
        observed = date.fromisoformat(observed_session)
        expected = date.fromisoformat(expected_completed_session)
        if observed.isoformat() != observed_session or expected.isoformat() != expected_completed_session:
            raise ValueError("noncanonical_date")
    except (TypeError, ValueError):
        return {"status": "DATA_BLOCKED", "reason": "invalid_session"}
    if provider_verified is not True:
        return {"status": "DATA_BLOCKED", "reason": "provider_unverified"}
    if observed != expected:
        return {"status": "DATA_BLOCKED", "reason": "unexpected_completed_session"}
    return {"status": "SESSION_MATCH", "observed_session": observed_session,
            "exchange_calendar_independently_verified": False,
            "final_bar_independently_verified": False,
            "trade_ready": False}
