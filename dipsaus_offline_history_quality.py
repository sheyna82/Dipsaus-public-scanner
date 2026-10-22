"""Conservative, descriptive checks for suspicious gaps and close-to-close jumps.

Never infer missing sessions from weekdays alone: exchange holidays exist.
Never automatically repair or label a price jump as a stock split.
"""
from datetime import date


def audit_price_history(bars, *, jump_threshold_pct=35.0, gap_calendar_days=7):
    if not 0 < jump_threshold_pct < 100 or gap_calendar_days < 4:
        raise ValueError("invalid_thresholds")
    findings = []
    for previous, current in zip(bars, bars[1:]):
        earlier = date.fromisoformat(previous["date"])
        later = date.fromisoformat(current["date"])
        if later <= earlier:
            raise ValueError("unsorted_dates")
        gap = (later - earlier).days
        if gap > gap_calendar_days:
            findings.append({"type": "CALENDAR_GAP_REVIEW", "from": earlier.isoformat(),
                             "to": later.isoformat(), "calendar_days": gap,
                             "missing_trading_sessions_confirmed": False})
        old_close, new_close = float(previous["close"]), float(current["close"])
        if old_close <= 0 or new_close <= 0:
            raise ValueError("invalid_close")
        change_pct = (new_close / old_close - 1) * 100
        if abs(change_pct) >= jump_threshold_pct:
            findings.append({"type": "PRICE_JUMP_REVIEW", "from": earlier.isoformat(),
                             "to": later.isoformat(), "close_change_pct": round(change_pct, 4),
                             "corporate_action_confirmed": False})
    return {"status": "REVIEW_ONLY", "findings": findings,
            "safe_for_prediction": not findings,
            "exchange_calendar_verified": False,
            "corporate_actions_verified": False}
