"""Local-only exchange_calendars 4.13.2 session export.

Requires a separately vetted installation of exactly exchange_calendars 4.13.2.
Never installs packages, downloads data, or accesses live trading credentials.
"""
import argparse
import hashlib
import json
from pathlib import Path


def export_sessions(exchange, start, end):
    import exchange_calendars as xcals
    if xcals.__version__ != "4.13.2":
        raise ValueError("unreviewed_calendar_version")
    if exchange not in ("XNYS", "XAMS"):
        raise ValueError("unsupported_exchange")
    calendar = xcals.get_calendar(exchange)
    sessions = calendar.sessions_in_range(start, end)
    dates = [value.date().isoformat() for value in sessions]
    canonical = json.dumps(dates, separators=(",", ":"), ensure_ascii=True)
    return {"exchange": exchange, "calendar_library": "exchange_calendars",
            "calendar_version": xcals.__version__,
            "session_dates": dates,
            "source_sha256": hashlib.sha256(canonical.encode("ascii")).hexdigest(),
            "digest_scope": "canonical_session_dates_json",
            "calendar_provenance_verified": False}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--exchange", choices=["XNYS", "XAMS"], required=True)
    parser.add_argument("--start", required=True)
    parser.add_argument("--end", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    result = export_sessions(args.exchange, args.start, args.end)
    output = Path(args.output)
    if output.exists():
        raise ValueError("refuse_overwrite")
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
