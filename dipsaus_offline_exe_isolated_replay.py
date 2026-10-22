"""Descriptive EXE replay within isolated, complete minute spans only.

Each gap resets the indicator history. Signals never borrow observations from
a previous span. No inference about full-session warning lead time.
"""
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from portfolio_downside_research import replay_intraday

NY = ZoneInfo("America/New_York")
FIELDS = ("open", "high", "low", "close")


def replay_isolated_spans(timestamps, quote, session):
    try:
        spans = []
        current = []
        last = None
        rejected = 0
        for i, stamp in enumerate(timestamps):
            ts = datetime.fromtimestamp(stamp, timezone.utc)
            ny = ts.astimezone(NY)
            if ny.date().isoformat() != session or not 570 <= ny.hour*60+ny.minute < 960:
                continue
            vals = [quote[k][i] for k in FIELDS]
            if (ts.second != 0 or any(type(v) not in (int, float) or not 0 < v < float("inf") for v in vals)
                    or not vals[2] <= min(vals[0], vals[3]) <= max(vals[0], vals[3]) <= vals[1]):
                rejected += 1
                if current:
                    spans.append(current)
                    current = []
                last = None
                continue
            if last is not None and (ts-last).total_seconds() != 60:
                if current:
                    spans.append(current)
                current = []
            current.append((ts, dict(zip(FIELDS, vals))))
            last = ts
        if current:
            spans.append(current)
        results = []
        for span in spans:
            replay = replay_intraday([bar for _, bar in span], enabled=True)
            idx = replay["first_signal_index"]
            results.append({"start_ny": span[0][0].astimezone(NY).isoformat(),
                            "end_ny": span[-1][0].astimezone(NY).isoformat(),
                            "bars": len(span), "status": replay["status"],
                            "first_signal_available_utc":
                                (span[idx][0].isoformat() if idx is not None else None),
                            "signal_bar_count": replay["signal_count"]})
        return {"status": "ISOLATED_SPANS_RESEARCH", "session": session,
                "spans": results, "rejected_bars": rejected,
                "history_resets_at_gaps": True,
                "full_session_replay_permitted": False,
                "predictive_edge_proven": False, "trade_ready": False}
    except (ValueError, TypeError, KeyError, IndexError, OverflowError, OSError):
        return {"status": "DATA_BLOCKED", "reason": "invalid_input", "trade_ready": False}
