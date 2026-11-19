"""Replay the pinned user-supplied ISO 10383 snapshot locally, never trading.

Usage:
  python research_iso_replay.py /path/to/ISO10383_MIC.csv --as-of 2026-11-23
The CSV bytes are not included in this repository.
"""
import argparse
import json
from datetime import date
from pathlib import Path
from research_iso_official_snapshot import inspect_official_mic_csv

PINNED_SHA256 = "74cc23bb951c6cc0c2f2f8af60e97e63e36093d5f599975ad1b90311d9daea2b"
SELECTED_MICS = ("XETR", "XETA", "XETB", "XAMS", "XHEL")


def replay(raw, *, as_of):
    return inspect_official_mic_csv(
        raw,
        expected_sha256=PINNED_SHA256,
        publication_date=date(2026, 11, 9),
        effective_date=date(2026, 11, 23),
        as_of=as_of,
        requested_mics=SELECTED_MICS,
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv_path", type=Path)
    parser.add_argument("--as-of", type=date.fromisoformat, required=True)
    args = parser.parse_args()
    result = replay(args.csv_path.read_bytes(), as_of=args.as_of)
    print(json.dumps(result, sort_keys=True, indent=2))
    return 0 if result["status"] == "OFFLINE_ISO_MIC_RECORDS_CONSISTENT" else 1


if __name__ == "__main__":
    raise SystemExit(main())
