"""Research-only liquidity and earnings risk screening; no source authentication.

Earnings session counts must come from a separately checked exchange calendar.
Neither self-reported calendar counts nor quote metadata verify real-world facts.
"""
import math

BLOCKED = {"trade_ready": False, "order_placement_enabled": False,
           "source_authenticity_independently_verified": False}

def screen_research_risks(data):
    base = {**BLOCKED, "status": "RISK_DATA_BLOCKED"}
    if not isinstance(data, dict):
        return {**base, "reason": "INVALID_INPUT"}
    keys = ("bid", "ask", "average_daily_turnover_eur", "relative_volume")
    if any(type(data.get(k)) not in (int, float)
           or not math.isfinite(data[k]) for k in keys):
        return {**base, "reason": "INVALID_LIQUIDITY_NUMBERS"}
    bid, ask = data["bid"], data["ask"]
    turnover, rvol = data["average_daily_turnover_eur"], data["relative_volume"]
    if bid <= 0 or ask < bid or turnover < 0 or rvol < 0:
        return {**base, "reason": "INVALID_LIQUIDITY_RANGE"}
    spread_pct = 100 * (ask - bid) / ((ask + bid) / 2)
    if not math.isfinite(spread_pct):
        return {**base, "reason": "NUMERIC_OVERFLOW"}
    sessions = data.get("sessions_until_earnings")
    if sessions is not None and (type(sessions) is not int or sessions < 0):
        return {**base, "reason": "INVALID_EARNINGS_SESSION_COUNT"}
    if data.get("earnings_calendar_checked") is not True:
        sessions = None
    # Provisional research thresholds, not empirically calibrated.
    liquidity_warning = (spread_pct > 0.5 or turnover < 1_000_000 or rvol < 1)
    earnings_warning = sessions is not None and sessions <= 5
    return {**BLOCKED, "status": "RESEARCH_RISK_SCREEN_ONLY",
            "spread_pct": round(spread_pct, 4),
            "liquidity_warning": liquidity_warning,
            "earnings_within_five_sessions": earnings_warning if sessions is not None else None,
            "earnings_calendar_independently_verified": False,
            "risk_data_complete": sessions is not None,
            "research_priority": ("DEFER_FOR_REVIEW" if liquidity_warning or earnings_warning
                                  else "REVIEW_EARNINGS_UNKNOWN" if sessions is None
                                  else "ELIGIBLE_FOR_FURTHER_RESEARCH"),
            "thresholds_calibrated": False}
