"""Offline CLI for redacted event-quote evidence-gap counts.

Usage: python event_quote_gap_cli.py INPUT.json --now 2026-11-02T15:00:00+00:00
Input is a local JSON list of watch rows, or {"rows": [...]}. No network.
Output contains only aggregate counts; never print raw input or exception details.
"""
import argparse
from datetime import datetime
import json
import sys
from event_quote_gap_summary import summarize_event_quote_gaps

def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", help="Local JSON report (never uploaded)")
    parser.add_argument("--now", required=True, help="Timezone-aware ISO 8601 timestamp")
    parser.add_argument("--currency", default="USD", choices=("USD", "EUR", "GBP", "CHF"))
    args = parser.parse_args(argv)
    try:
        now = datetime.fromisoformat(args.now.replace("Z", "+00:00"))
        if now.tzinfo is None or now.utcoffset() is None:
            raise ValueError("timezone required")
        with open(args.input, encoding="utf-8") as stream:
            payload = json.load(stream)
        rows = payload.get("rows") if isinstance(payload, dict) else payload
        result = summarize_event_quote_gaps(rows, now, args.currency)
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        print(json.dumps({"status": "INPUT_ERROR", "execution_ready": False}))
        return 2
    print(json.dumps(result, sort_keys=True))
    return 0 if result["status"] == "RESEARCH_ONLY" else 2

if __name__ == "__main__":
    sys.exit(main())
