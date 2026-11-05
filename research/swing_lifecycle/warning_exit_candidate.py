"""Research-only bridge from dated close warnings to next-open exit candidates.

This adapter never places orders, does not certify fills, and requires a caller
to validate corporate actions, event timestamps, FX and costs independently.
"""
from datetime import date
from research_swing_failure_warning import failure_warning_at_close


def warning_exit_candidate(bars, *, ticker, entry_index, baseline_exit_index,
                           lookback=20, min_hold=3, confirmation_sessions=1):
    """Find earliest warning close after entry; propose next-session-open exit.

    bars are chronological, session-dated OHLC dictionaries with 'date' as
    ISO YYYY-MM-DD. Entry and baseline exit occur at session open. A signal
    on close[t] can only cause an exit at open[t+1].
    """
    if not isinstance(ticker, str) or not ticker.strip():
        raise ValueError("invalid_ticker")
    if type(entry_index) is not int or type(baseline_exit_index) is not int:
        raise ValueError("invalid_indices")
    if type(min_hold) is not int or min_hold < 1:
        raise ValueError("invalid_min_hold")
    if type(confirmation_sessions) is not int or confirmation_sessions < 1:
        raise ValueError("invalid_confirmation_sessions")
    if not isinstance(bars, (list, tuple)) or not (
        0 <= entry_index < baseline_exit_index < len(bars)
    ):
        raise ValueError("invalid_window")
    dates = []
    for bar in bars:
        if not isinstance(bar, dict) or not isinstance(bar.get("date"), str):
            raise ValueError("missing_session_date")
        d = date.fromisoformat(bar["date"])
        if dates and d <= dates[-1]:
            raise ValueError("nonchronological_sessions")
        dates.append(d)
    first_decision = max(entry_index, lookback, entry_index + min_hold - 1)
    consecutive = 0
    for t in range(first_decision, baseline_exit_index):
        signal = failure_warning_at_close(bars, t, lookback=lookback)
        consecutive = consecutive + 1 if signal["warning"] else 0
        if consecutive >= confirmation_sessions:
            return {
                "ticker": ticker,
                "entry_date": dates[entry_index].isoformat(),
                "baseline_exit_date": dates[baseline_exit_index].isoformat(),
                "candidate_exit_date": dates[t + 1].isoformat(),
                "warning_decision_date": dates[t].isoformat(),
                "baseline_holding_sessions": baseline_exit_index - entry_index,
                "candidate_holding_sessions": t + 1 - entry_index,
                "warning_details": signal,
                "confirmation_sessions": confirmation_sessions,
                "research_only": True,
                "trade_ready": False,
                "fill_verified": False,
                "costs_and_fx_verified": False,
            }
    return {
        "ticker": ticker,
        "entry_date": dates[entry_index].isoformat(),
        "baseline_exit_date": dates[baseline_exit_index].isoformat(),
        "candidate_exit_date": dates[baseline_exit_index].isoformat(),
        "warning_decision_date": None,
        "baseline_holding_sessions": baseline_exit_index - entry_index,
        "candidate_holding_sessions": baseline_exit_index - entry_index,
        "warning_details": None,
        "confirmation_sessions": confirmation_sessions,
        "research_only": True,
        "trade_ready": False,
        "fill_verified": False,
        "costs_and_fx_verified": False,
    }
