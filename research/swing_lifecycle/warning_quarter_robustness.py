"""Research-only leave-one-quarter-out robustness for warning risk case CSV.

Descriptive stability check, NOT out-of-sample model validation.
Usage: python -m research.swing_lifecycle.warning_quarter_robustness reports/warning-real-pilot/warning_risk_cases.csv --output reports/warning-real-pilot/warning_quarter_robustness.json
"""
import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path
from statistics import mean


def evaluate(csv_path):
    groups = defaultdict(list)
    with open(csv_path, newline="", encoding="utf-8") as stream:
        for row in csv.DictReader(stream):
            rule = int(row["confirmation_sessions"])
            quarter = row["entry_quarter"]
            groups[rule].append((quarter, float(row["return_difference_pp"]),
                                 float(row["candidate_mae_pct"]),
                                 float(row["baseline_mae_pct"])))
    if not groups:
        raise ValueError("no_cases")
    output = {"method": "leave_one_entry_quarter_out_descriptive",
              "research_only": True, "independent_validation": False,
              "rules": {}}
    for rule, rows in sorted(groups.items()):
        quarters = sorted({r[0] for r in rows})
        if len(quarters) < 2:
            raise ValueError("insufficient_quarters")
        full = mean(r[1] for r in rows)
        excluded = {}
        for quarter in quarters:
            subset = [r for r in rows if r[0] != quarter]
            excluded[quarter] = {"n": len(subset),
                                 "mean_return_difference_pp": mean(r[1] for r in subset)}
        output["rules"][str(rule)] = {
            "n": len(rows), "quarters": len(quarters),
            "mean_return_difference_pp": full,
            "mean_mae_improvement_pp": mean(r[2] - r[3] for r in rows),
            "leave_one_quarter_out": excluded,
            "positive_exclusions": sum(v["mean_return_difference_pp"] > 0
                                       for v in excluded.values()),
        }
    return output


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("csv_path", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = evaluate(args.csv_path)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({"rules": list(report["rules"])}))
