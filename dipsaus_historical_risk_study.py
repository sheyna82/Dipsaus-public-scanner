"""Offline chronological historical-bar adapter, without downloads or alerts."""
from datetime import date
from dipsaus_risk_scenario_study import study_scenario


def study_historical_bars(rows, signal_index, lookahead_sessions=5):
    """Evaluate future *completed* daily closes against pre-signal reference.

    Does not simulate fills, predict trades, or assert adjusted OHLC provenance.
    Caller must independently verify split adjustment and source before use.
    """
    if (not isinstance(rows, (list, tuple)) or type(signal_index) is not int
            or type(lookahead_sessions) is not int or lookahead_sessions < 1
            or signal_index < 14 or signal_index + lookahead_sessions >= len(rows)):
        return None
    dates = []
    for bar in rows:
        if not isinstance(bar, dict):
            return None
        try:
            day = date.fromisoformat(bar["date"])
        except (ValueError, TypeError, KeyError):
            return None
        if dates and day <= dates[-1]:
            return None
        dates.append(day)
    history = list(rows[:signal_index + 1])
    future = list(rows[signal_index + 1:signal_index + 1 + lookahead_sessions])
    entry = history[-1].get("close")
    if type(entry) not in (int, float):
        return None
    outcome = study_scenario(history, entry, [bar.get("close") for bar in future])
    if outcome is None:
        return None
    return {
        "signal_date": rows[signal_index]["date"],
        "observation_dates": [bar["date"] for bar in future],
        "risk_states": [x["risk_state"] for x in outcome["observations"]],
        "source_verified": False,
        "split_adjustment_verified": False,
        "historical_performance_claim": False,
        "research_only": True,
        "trade_ready": False,
        "automatic_sell": False,
        "stop_order_created": False,
    }
