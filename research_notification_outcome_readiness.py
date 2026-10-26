"""Calendar-aware research maturity gate for post-notification daily outcomes.

Counts actual subsequent observed sessions, never calendar days. Excludes the
signal date because phone screenshots lack verified UTC execution timestamps.
"""
from datetime import datetime,timezone

def outcome_readiness(signal_day,bars,horizons=(3,5,10,20)):
    if datetime.strptime(signal_day,"%Y-%m-%d").strftime("%Y-%m-%d")!=signal_day:
        raise ValueError("invalid_signal_day")
    dates=[]
    for bar in bars:
        ts=bar.get("timestamp")
        if not isinstance(ts,int):
            raise ValueError("invalid_timestamp")
        day=datetime.fromtimestamp(ts,timezone.utc).date().isoformat()
        if day>signal_day:
            dates.append(day)
    if dates!=sorted(set(dates)):
        raise ValueError("duplicate_or_unsorted_sessions")
    return {"signal_day":signal_day,"observed_subsequent_sessions":len(dates),
            "horizons":{str(h):{"ready":len(dates)>=h,
                                "earliest_exit_session":dates[h-1] if len(dates)>=h else None}
                        for h in horizons},
            "execution_verified":False,"trade_ready":False,"research_only":True,
            "caveat":"A mature horizon is not a verified executable return."}
