"""Retrospective EXE downside lead-time audit; never used to generate signals.

An alert is available only after its signal candle closes. Subsequent loss
threshold crossings are measured from the session's first open, not fitted.
This is descriptive timing, not evidence of predictive performance.
"""
from datetime import timedelta
from portfolio_downside_research import replay_intraday


def audit_downside_lead_time(timestamped_bars, *, decline_pct=3):
    if not isinstance(timestamped_bars, list) or len(timestamped_bars) < 31:
        return {"status": "DATA_BLOCKED", "reason": "insufficient_bars",
                "trade_ready": False}
    if type(decline_pct) not in (int, float) or not 0 < decline_pct <= 20:
        return {"status": "DATA_BLOCKED", "reason": "invalid_threshold",
                "trade_ready": False}
    try:
        if any((timestamped_bars[i+1][0]-timestamped_bars[i][0]).total_seconds() != 60
               for i in range(len(timestamped_bars)-1)):
            raise ValueError("missing_or_duplicate_minute")
        first_open = float(timestamped_bars[0][1]["open"])
        if first_open <= 0:
            raise ValueError("invalid_open")
        bars = [bar for _, bar in timestamped_bars]
        replay = replay_intraday(bars, enabled=True)
        if replay["status"] != "RESEARCH_ONLY":
            raise ValueError("invalid_ohlc")
        threshold = first_open * (1-decline_pct/100)
        # A crossing in candle i becomes observable at its close, not at its start.
        crossing = next((i for i, (_, bar) in enumerate(timestamped_bars)
                         if float(bar["low"]) <= threshold), None)
        signal = replay["first_signal_index"]
        alert_available = timestamped_bars[signal][0] + timedelta(minutes=1) if signal is not None else None
        crossing_observable = timestamped_bars[crossing][0] + timedelta(minutes=1) if crossing is not None else None
        lead = ((crossing_observable-alert_available).total_seconds()/60
                if alert_available is not None and crossing_observable is not None else None)
        return {"status": "DESCRIPTIVE_LEAD_TIME", "bars": len(bars),
                "decline_threshold_pct": decline_pct,
                "first_signal_available_utc": alert_available.isoformat() if alert_available else None,
                "first_decline_observable_utc": crossing_observable.isoformat() if crossing_observable else None,
                "lead_minutes": lead,
                "alert_before_decline": lead > 0 if lead is not None else None,
                "threshold_uses_first_session_open": True,
                "source_data_verified": False, "predictive_edge_proven": False,
                "trade_ready": False}
    except (ValueError, TypeError, KeyError, IndexError, OverflowError):
        return {"status": "DATA_BLOCKED", "reason": "invalid_or_gapped_bars",
                "trade_ready": False}
