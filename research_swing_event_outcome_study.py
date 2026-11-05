"""Offline event outcome study: verified news -> session close -> next open.

Descriptive historical labels only. No calibrated probabilities or trade orders.
"""
from research_swing_event_session_alignment import align_event_to_sessions
from research_swing_event_downside import event_downside_outcomes


def study_event_outcomes(event, sessions, bars, *, horizons=(3, 5, 10, 15),
                         decision_lag_seconds=0, cost_bps_roundtrip=30,
                         slippage_bps_per_side=10):
    """Align news availability to a decision close, then label future outcomes.

    Each OHLC bar must correspond one-to-one to the ordered sessions.
    Returns no outcomes when no future exit session is available.
    """
    if len(sessions) != len(bars):
        raise ValueError("session_bar_length_mismatch")
    alignment = align_event_to_sessions(
        event, sessions, decision_lag_seconds=decision_lag_seconds)
    if alignment is None:
        return {"alignment": None, "outcomes": [], "trade_ready": False}
    index = alignment["known_session_index"]
    if index + 2 >= len(bars):
        return {"alignment": alignment, "outcomes": [], "trade_ready": False}
    outcomes = event_downside_outcomes(
        bars, known_session_index=index, horizons=horizons,
        cost_bps_roundtrip=cost_bps_roundtrip,
        slippage_bps_per_side=slippage_bps_per_side)
    return {"alignment": alignment, "outcomes": outcomes, "trade_ready": False}
