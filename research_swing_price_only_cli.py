"""Run the price-only benchmark on locally held real historical OHLC CSV files.

Example:
 python research_swing_price_only_cli.py --prices AAPL=aapl.csv ASML=asml.csv --output results.json

This is a descriptive historical study, not a signal or a data downloader.
"""
import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from research_swing_event_price_csv_bridge import load_verified_price_csv
from research_swing_price_only_recovery_benchmark import recovery_vs_unconditional


def run_price_csv_study(paths, *, horizons=(3, 5, 10, 15),
                        lookback=20, dip_pct=10, cost_bps=50):
    if not isinstance(paths, dict) or not paths:
        raise ValueError("missing_price_universe")
    prices, sources = {}, {}
    for symbol, raw_path in sorted(paths.items()):
        if not isinstance(symbol, str) or not symbol.strip():
            raise ValueError("invalid_symbol")
        path = Path(raw_path)
        raw = path.read_bytes()
        prices[symbol] = load_verified_price_csv(path)
        sources[symbol] = {"filename": path.name,
                           "sha256": hashlib.sha256(raw).hexdigest(),
                           "bar_count": len(prices[symbol]),
                           "first_session": prices[symbol][0]["open_at"],
                           "last_session": prices[symbol][-1]["close_at"]}
    result = recovery_vs_unconditional(
        prices, horizons=horizons, lookback=lookback,
        dip_pct=dip_pct, cost_bps=cost_bps)
    result["sources"] = sources
    result["methodology_limits"] = [
        "Historical descriptive results; no out-of-sample edge proven",
        "CSV data provenance, adjustments, delistings and license require external audit",
        "Baseline observations overlap and are not independent",
        "Price-only study does not include event-time research",
        "No portfolio allocation, liquidity model or currency conversion",
    ]
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prices", nargs="+", required=True, metavar="SYMBOL=CSV")
    parser.add_argument("--output", required=True)
    parser.add_argument("--lookback", type=int, default=20)
    parser.add_argument("--dip-pct", type=float, default=10)
    parser.add_argument("--cost-bps", type=float, default=50)
    args = parser.parse_args()
    paths = {}
    for item in args.prices:
        if "=" not in item:
            parser.error("Each --prices item must be SYMBOL=CSV")
        symbol, filename = item.split("=", 1)
        if not symbol or not filename or symbol in paths:
            parser.error("Missing or duplicate symbol")
        paths[symbol] = filename
    result = run_price_csv_study(paths, lookback=args.lookback,
                                 dip_pct=args.dip_pct, cost_bps=args.cost_bps)
    Path(args.output).write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print("Measured", len(result["sources"]), "symbols; output:", args.output)


if __name__ == "__main__":
    main()
