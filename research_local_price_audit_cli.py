"""Offline-only command line audit for a locally held licensed OHLCV CSV.

Reads local files, emits metadata only. No networking, no price rows in output.
Never treat structural acceptance as source authentication.
"""
import argparse
import json
from pathlib import Path

from research_historical_price_ingest_gate import audit_historical_price_dataset


def audit_local_files(manifest_path, csv_path):
    manifest = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
    payload = Path(csv_path).read_bytes()
    return audit_historical_price_dataset(manifest, payload)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True, help="Local manifest JSON path")
    parser.add_argument("--csv", required=True, help="Local daily OHLCV CSV path")
    args = parser.parse_args(argv)
    try:
        result = audit_local_files(args.manifest, args.csv)
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        # Avoid printing file content or full paths in exception messages.
        print(json.dumps({"accepted": False, "error_type": type(exc).__name__,
                          "research_data_ready": False, "trade_ready": False},
                         sort_keys=True))
        return 1
    # No source path, raw bars, provider URL, or license text is printed.\n    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
