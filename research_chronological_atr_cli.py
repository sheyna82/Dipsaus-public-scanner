"""Local-only chronological ATR comparison CLI. No network or order execution.

Never uploads input prices, prints rows, or claims independent validation.
Output is descriptive until source, PIT, and corporate-action checks pass.
"""
import argparse
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
    result = evaluate_chronological_csv(
        args.stock_csv.read_bytes(), args.benchmark_csv.read_bytes(),
        split_date=args.split_date, horizon=args.horizon,
        threshold=args.threshold, embargo_seconds=args.embargo_days * 86400)
    print(json.dumps(result, sort_keys=True))
    return result


if __name__ == "__main__":
    main()
