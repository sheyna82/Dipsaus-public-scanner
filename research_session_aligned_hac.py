"""Research-only contiguous-block HAC input gate.

A calendar gap is not necessarily a missing trading session. Require a
caller-supplied verified exchange session calendar, and refuse otherwise.
"""
from datetime import date
from research_paired_brier_hac import paired_brier_hac


def evaluate_session_aligned_hac(predictions, *, session_dates, lags,
                                 horizon_sessions):
    if not isinstance(predictions, (list, tuple)) or not predictions:
        raise ValueError("invalid_predictions")
    if not isinstance(session_dates, (list, tuple)) or len(session_dates) != len(predictions):
        raise ValueError("invalid_session_dates")
    if type(horizon_sessions) is not int or horizon_sessions < 1:
        raise ValueError("invalid_horizon")
    parsed = []
    for day in session_dates:
        if not isinstance(day, str):
            raise ValueError("invalid_session_date")
        try:
            parsed.append(date.fromisoformat(day))
        except ValueError as exc:
            raise ValueError("invalid_session_date") from exc
    if any(b <= a for a, b in zip(parsed, parsed[1:])):
        raise ValueError("unordered_or_duplicate_sessions")
    # The caller must establish that this ordered sequence includes every
    # eligible exchange session. Calendar days alone cannot establish this.
    result = paired_brier_hac(predictions, lags=lags)
    result.update({"session_calendar_verified": False,
                   "session_continuity_verified": False,
                   "horizon_sessions": horizon_sessions,
                   "lags_cover_full_label_overlap": lags >= horizon_sessions - 1,
                   "statistical_significance_verified": False,
                   "trade_ready": False})
    return result
