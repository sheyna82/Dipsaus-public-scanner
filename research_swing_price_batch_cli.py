"""Research-only single-command local price-data audit.

Use after obtaining CSV files from a provider whose access and licensing
have been independently checked. Does not fetch or redistribute data.
"""
import argparse
import json
from pathlib import Path
from research_swing_price_batch_manifest import create_price_batch_manifest


def main(argv=None):
    parser = argparse.ArgumentParser(description="Audit local historical OHLCV CSV batch")
    parser.add_argument("--provider", required=True)
    parser.add_argument("--retrieved-at", required=True)
    parser.add_argument("--file", action="append", required=True,
                        metavar="SYMBOL=CSV_PATH")
    parser.add_argument("--manifest-out", required=True)
    args = parser.parse_args(argv)
    files = {}
    for entry in args.file:
        if "=" not in entry:
            parser.error("--file must be SYMBOL=CSV_PATH")
        symbol, path = entry.split("=", 1)
        if not symbol.strip() or not path.strip() or symbol in files:
            parser.error("invalid or duplicate symbol")
        files[symbol] = path
    result = create_price_batch_manifest(
        files, provider_name=args.provider, retrieved_at=args.retrieved_at)
    destination = Path(args.manifest_out)
    if destination.exists():
        raise ValueError("manifest_destination_already_exists")
    destination.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                           encoding="utf-8")
    return result


if __name__ == "__main__":
    main()
