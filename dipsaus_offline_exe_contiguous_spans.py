"""Describe intact EXE minute spans; never fill or replay missing prices."""
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

NY = ZoneInfo("America/New_York")
FIELDS = ("open", "high", "low", "close")


def valid_contiguous_spans(timestamps, quote, session):
    try:
        valid = []
        rejected = []
        for i, stamp in enumerate(timestamps):
            dt = datetime.fromtimestamp(stamp, timezone.utc)
            ny = dt.astimezone(NY)
            if ny.date().isoformat() != session or not 570 <= ny.hour*60+ny.minute < 960:
                continue
            vals = [quote[k][i] for k in FIELDS]
            if any(type(v) not in (float, int) or not 0 < v < float("inf") for v in vals):
                rejected.append(ny.isoformat())
                continue
            op, hi, lo, close = vals
            if not lo <= min(op, close) <= max(op, close) <= hi:
                rejected.append(ny.isoformat())
                continue
            valid.append(dt)
        spans = []
        for dt in valid:
            if spans and (dt - spans[-1][-1]).total_seconds() == 60:
                spans[-1].append(dt)
            else:
                spans.append([dt])
        return {"status": "PARTIAL_DIAGNOSTIC_ONLY", "session": session,
                "valid_bar_count": len(valid), "rejected_minutes_ny": rejected[:25],
                "rejected_count": len(rejected),
                "contiguous_spans": [{"start_ny": x[0].astimezone(NY).isoformat(),
                                      "end_ny": x[-1].astimezone(NY).isoformat(),
                                      "bars": len(x)} for x in spans],
                "full_session_replay_permitted": False, "synthetic_bars_created": 0,
                "trade_ready": False}
    except (KeyError, IndexError, TypeError, ValueError, OverflowError, OSError):
        return {"status": "DATA_BLOCKED", "reason": "invalid_input", "trade_ready": False}
