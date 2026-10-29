"""Offline historical CSV benchmark. No network, orders or fabricated market data.

Manifest columns: ticker,csv_path,entry_date,baseline_exit_date,score
Paths are resolved relative to manifest location. All dates are trading sessions.
Each row is a predeclared candidate; do not select entries using future returns.
"""
import argparse
import csv
import json
from datetime import date
from pathlib import Path
from research.swing_lifecycle.ohlc_csv_loader import load_daily_ohlc_csv
from research.swing_lifecycle.warning_exit_holdout import evaluate_warning_exit_holdout


def run_historical_csv_benchmark(manifest, *, cutoff, source,
                                 embargo_days=15, cost_bps_per_side=10):
    manifest = Path(manifest)
    cases = []
    with manifest.open(newline="", encoding="utf-8-sig") as stream:
        reader = csv.DictReader(stream)
        required = {"ticker", "csv_path", "entry_date", "baseline_exit_date", "score"}
        if not required.issubset(reader.fieldnames or []):
            raise ValueError("missing_manifest_columns")
        for record in reader:
            path = (manifest.parent / record["csv_path"]).resolve()
            if not path.is_relative_to(manifest.parent.resolve()):
                raise ValueError("csv_path_outside_manifest_directory")
            loaded = load_daily_ohlc_csv(path, source=source,
                                         ticker=record["ticker"])
            bars = loaded["bars"]
            indices = {bar["date"]: i for i, bar in enumerate(bars)}
            try:
                entry = indices[record["entry_date"]]
                exit_index = indices[record["baseline_exit_date"]]
            except KeyError as exc:
                raise ValueError("manifest_date_not_a_session") from exc
            if entry >= exit_index:
                raise ValueError("invalid_trade_window")
            cases.append({"ticker": record["ticker"], "bars": bars,
                          "entry_index": entry,
                          "baseline_exit_index": exit_index,
                          "score": float(record["score"])})
    if not cases:
        raise ValueError("empty_manifest")
    report = evaluate_warning_exit_holdout(
        cases, cutoff=cutoff, embargo_days=embargo_days,
        cost_bps_per_side=cost_bps_per_side)
    report["input_manifest"] = str(manifest)
    report["source_label"] = source
    report["market_data_provenance_verified"] = False
    report["candidate_selection_independently_verified"] = False
    report["historical_edge_proven"] = False
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--cutoff", type=date.fromisoformat, required=True)
    parser.add_argument("--source", required=True)
    parser.add_argument("--embargo-days", type=int, default=15)
    parser.add_argument("--cost-bps-per-side", type=float, default=10)
    args = parser.parse_args()
    result = run_historical_csv_benchmark(
        args.manifest, cutoff=args.cutoff, source=args.source,
        embargo_days=args.embargo_days,
        cost_bps_per_side=args.cost_bps_per_side)
    print(json.dumps(result, indent=2, sort_keys=True, default=str))


if __name__ == "__main__":
    main()
