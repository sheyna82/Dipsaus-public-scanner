"""Bounded research-only EXE historical minute replay from public source.

Fail closed on missing session minutes, unfinished candles or invalid OHLC.
No signals, notifications, trades or data persistence.
"""
import json
from datetime import datetime, timezone
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo
from research_probe_exe_minute_source import URL
from dipsaus_offline_exe_lead_time_audit import audit_downside_lead_time
from dipsaus_offline_exe_missing_minutes import audit_regular_session_timestamps

NY = ZoneInfo("America/New_York")
TARGET = "2026-10-21"


def evaluate_payload(payload, session=TARGET):
    try:
        result = payload["chart"]["result"][0]
        times = result["timestamp"]
        quote = result["indicators"]["quote"][0]
        if any(len(quote[k]) != len(times) for k in ("open", "high", "low", "close")):
            raise ValueError("mismatched_lengths")
        grid = audit_regular_session_timestamps(times, session)
        if grid["status"] != "COMPLETE":
            return {"symbol": "EXE", "session": session, "status": "DATA_BLOCKED",
                    "reason": "incomplete_regular_session", "minute_audit": grid,
                    "source_independently_verified": False, "trade_ready": False}
        rows = []
        for i, stamp in enumerate(times):
            utc = datetime.fromtimestamp(stamp, timezone.utc)
            ny = utc.astimezone(NY)
            if ny.date().isoformat() != session:
                continue
            if not (9 * 60 + 30 <= ny.hour * 60 + ny.minute < 16 * 60):
                continue
            bar = {k: quote[k][i] for k in ("open", "high", "low", "close")}
            if any(type(v) not in (float, int) or v <= 0 for v in bar.values()):
                raise ValueError("missing_bar")
            if not bar["low"] <= min(bar["open"], bar["close"]) <= max(bar["open"], bar["close"]) <= bar["high"]:
                raise ValueError("invalid_ohlc")
            if utc.second != 0 or utc.microsecond != 0:
                raise ValueError("unfinished_bar")
            rows.append((utc, bar))
        if len(rows) != 390:
            raise ValueError("incomplete_regular_session")
        if any((rows[i+1][0] - rows[i][0]).total_seconds() != 60
               for i in range(len(rows)-1)):
            raise ValueError("gapped_session")
        audit = audit_downside_lead_time(rows, decline_pct=3)
        return {"symbol": "EXE", "session": session, **audit,
                "session_complete": True, "source_independently_verified": False,
                "trade_ready": False}
    except (KeyError, IndexError, TypeError, ValueError, OverflowError):
        return {"symbol": "EXE", "session": session, "status": "DATA_BLOCKED",
                "reason": "incomplete_or_invalid_session",
                "source_independently_verified": False, "trade_ready": False}


def run(fetch=None):
    try:
        if fetch is None:
            with urlopen(Request(URL, headers={"User-Agent": "DipsausResearchSourceCheck/1.0"}),
                         timeout=12) as response:
                raw = response.read(1_000_001)
        else:
            raw = fetch(URL)
        if len(raw) > 1_000_000:
            raise ValueError("oversized")
        return evaluate_payload(json.loads(raw))
    except (OSError, ValueError, TimeoutError, UnicodeError, TypeError):
        return {"symbol": "EXE", "session": TARGET, "status": "DATA_BLOCKED",
                "reason": "source_unavailable", "trade_ready": False}


if __name__ == "__main__":
    print(json.dumps(run(), sort_keys=True))
