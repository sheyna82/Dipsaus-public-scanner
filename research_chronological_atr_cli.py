"""Local-only chronological ATR comparison CLI. No network or order execution.

Never uploads input prices, prints rows, or claims independent validation.
Output is descriptive until source, PIT, and corporate-action checks pass.
"""
import argparse
import hashlib
import json
from pathlib import Path
from research_chronological_atr_experiment import evaluate_chronological_csv


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stock-csv", type=Path, required=True)
    parser.add_argument("--benchmark-csv", type=Path, required=True)
    parser.add_argument("--split-date", required=True)
    parser.add_argument("--horizon", type=int, default=10)
    parser.add_argument("--threshold", type=float, default=0.08)
    parser.add_argument("--embargo-days", type=int, default=0)
    args = parser.parse_args(argv)
    if args.stock_csv.resolve() == args.benchmark_csv.resolve():
        parser.error("stock and benchmark must be separate files")
    if args.embargo_days < 0:
        parser.error("embargo days must be nonnegative")
    stock_bytes = args.stock_csv.read_bytes()
    benchmark_bytes = args.benchmark_csv.read_bytes()
    result = evaluate_chronological_csv(
        stock_bytes, benchmark_bytes,
        split_date=args.split_date, horizon=args.horizon,
        threshold=args.threshold, embargo_seconds=args.embargo_days * 86400)
    result.update({
        "stock_sha256": hashlib.sha256(stock_bytes).hexdigest(),
        "benchmark_sha256": hashlib.sha256(benchmark_bytes).hexdigest(),
        "source_license_verified": False,
        "source_provenance_verified": False,
        "adjustments_verified": False,
        "survivorship_bias_cleared": False,
        "point_in_time_verified": False,
        "trade_ready": False,
    })
    print(json.dumps(result, sort_keys=True))
    return result


if __name__ == "__main__":
    main()
