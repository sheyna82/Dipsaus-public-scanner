"""Evaluate warning-risk excursions from archived EUR OHLCV provider bars.

Research-only calendar-spaced entries; no claim of executable strategy alpha.
"""
import argparse
import csv
import gzip
import json
from pathlib import Path

from research.swing_lifecycle.warning_risk_diagnostics import diagnose_case, summarize


def evaluate_archive(archive, output, *, holding_sessions=10, entry_stride=20):
    if not 5 <= holding_sessions <= 15 or entry_stride < holding_sessions:
        raise ValueError("invalid_sampling")
    rows = []
    with gzip.open(archive, "rt", encoding="utf-8") as stream:
        for line in stream:
            if not line.strip():
                continue
            record = json.loads(line)
            if record.get("currency") != "EUR":
                raise ValueError("non_eur_record")
            bars = []
            for raw in record["bars"]:
                day, op, high, low, close = raw[:5]
                bars.append({"date": day, "open": op, "high": high,
                             "low": low, "close": close})
            if len(bars) < 21 + holding_sessions:
                continue
            for i in range(21, len(bars) - holding_sessions, entry_stride):
                for confirmation in (1, 2, 3):
                    rows.append(diagnose_case(
                        bars, ticker=record["symbol"], entry_index=i,
                        baseline_exit_index=i + holding_sessions,
                        confirmation_sessions=confirmation))
    if not rows:
        raise ValueError("no_eligible_cases")
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    with (output / "warning_risk_cases.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    report = {"source": str(archive),
              "candidate_method": "calendar_spaced_not_scanner_signals",
              "currency": "EUR", "research_only": True,
              "independent_validation": False,
              "cases": len(rows), "summary": summarize(rows)}
    (output / "warning_risk_summary.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("archive", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = evaluate_archive(args.archive, args.output)
    print(json.dumps({"cases": result["cases"], "currency": result["currency"]}))
