"""Offline US session sanity checks, NOT an authoritative exchange calendar.

Weekend exclusion and timezone conversion are deterministic; holidays,
half-days, halts and exchange-specific sessions require independent evidence.
"""
from datetime import datetime
from zoneinfo import ZoneInfo

NY=ZoneInfo("America/New_York")

def review_us_session(*, observation_utc, claimed_session_date, official_calendar_verified=False):
    blocks=[]
    if not isinstance(observation_utc,str):
        instant=None
    else:
        try:
            instant=datetime.fromisoformat(observation_utc.replace("Z","+00:00"))
            if instant.tzinfo is None:instant=None
        except ValueError:
            instant=None
    if instant is None:blocks.append("OBSERVATION_TIME_UNRESOLVED")
    if not isinstance(claimed_session_date,str):
        session=None
    else:
        try:
            session=datetime.strptime(claimed_session_date,"%Y-%m-%d").date()
            if session.isoformat()!=claimed_session_date:session=None
        except ValueError:
            session=None
    if session is None:blocks.append("SESSION_DATE_UNRESOLVED")
    if instant and session and instant.astimezone(NY).date()!=session:
        blocks.append("NEW_YORK_SESSION_DATE_MISMATCH")
    if session and session.weekday()>=5:
        blocks.append("WEEKEND_NOT_REGULAR_SESSION")
    # Caller assertion alone is not independent exchange-calendar evidence.
    blocks.append("OFFICIAL_EXCHANGE_CALENDAR_UNVERIFIED")
    return {"status":"SHADOW_BLOCKED","blocks":sorted(set(blocks)),
            "calendar_verified":False,"trade_ready":False,"notify":False,
            "automatic_orders":False}
