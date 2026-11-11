"""Manual offline-research downloader CLI; never imported by live scanner.

Use only for public historical daily prices. Data are vendor-provided,
unverified and not suitable for trading decisions.
"""
import argparse
import json
from pathlib import Path
from research_event_stooq_acquisition import acquire_stooq_history


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start", required=True)
    parser.add_argument("--end", required=True)
    parser.add_argument("--output", default="research-event-history")
    parser.add_argument("--allow-network", action="store_true")
    args = parser.parse_args(argv)
    symbols = ("TSLA", "META", "COHU", "AMZN", "PLTR", "AMD", "SPY")
    output = Path(args.output)
    results = []
    for symbol in symbols:
        results.append(acquire_stooq_history(
            symbol, args.start, args.end, output,
            allow_network=args.allow_network))
    print(json.dumps({"research_only": True, "source_verified": False,
                      "files": results}, indent=2))


if __name__ == "__main__":
    main()
