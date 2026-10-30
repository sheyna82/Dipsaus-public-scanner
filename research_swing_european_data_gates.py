"""Research-only alignment and corporate-action caution gates.

Do not turn unadjusted OHLCV into verified tradable signals.
"""
from datetime import datetime, timezone
def validate_daily_rows(rows):
    if not rows: raise ValueError("empty_rows")
    dates=[];previous=None
    for row in rows:
        ts=row["timestamp"]
        if not isinstance(ts,int) or (previous is not None and ts<=previous):
            raise ValueError("timestamps_not_strictly_increasing")
        previous=ts
        day=datetime.fromtimestamp(ts,timezone.utc).date().isoformat()
        if day in dates: raise ValueError("duplicate_utc_date")
        dates.append(day)
        o,h,l,c=(float(row[k]) for k in ("open","high","low","close"))
        if not (0<l<=min(o,c)<=max(o,c)<=h):raise ValueError("invalid_ohlc")
    return dates
def aligned_dates(series_by_symbol):
    """Require identical dates; never align securities by positional index."""
    if not series_by_symbol:raise ValueError("empty_universe")
    calendars={symbol:validate_daily_rows(rows) for symbol,rows in series_by_symbol.items()}
    reference=next(iter(calendars.values()))
    if any(dates!=reference for dates in calendars.values()):
        raise ValueError("cross_market_calendar_mismatch")
    return reference
def require_corporate_action_review(metadata):
    """Explicit gate: raw Yahoo OHLCV is not split/dividend audited."""
    if metadata.get("split_audit") is not True or metadata.get("dividend_audit") is not True:
        raise ValueError("corporate_actions_unverified")
    return True
