"""Research-only capacity opportunity audit from an existing OOS report.

All historical outcomes are used only AFTER decisions have been made.
Never use this audit to rank candidates or generate orders.
"""
import json
from collections import defaultdict
from pathlib import Path


def summarize_capacity_opportunities(portfolio_report):
    if not isinstance(portfolio_report, dict):
        raise ValueError("INVALID_PORTFOLIO_REPORT")
    rows = portfolio_report.get("candidate_audit")
    if not isinstance(rows, list):
        raise ValueError("MISSING_CANDIDATE_AUDIT")
    output = {}
    for cohort in ("baseline", "filtered"):
        output[cohort] = {}
        for mode in ("symbol_asc", "symbol_desc", "stable_hash"):
            groups = defaultdict(list)
            competition_days = defaultdict(list)
            seen = set()
            for row in rows:
                key = (row["symbol"], row["entry_day"])
                if key in seen:
                    raise ValueError("DUPLICATE_CANDIDATE")
                seen.add(key)
                decision = row.get("priority_decisions", {}).get(cohort, {}).get(mode)
                if decision is None:
                    raise ValueError("MISSING_PRIORITY_DECISION")
                if decision == "NOT_IN_FILTERED_COHORT":
                    if cohort != "filtered" or row.get("filter_selected") is not False:
                        raise ValueError("INVALID_FILTER_EXCLUSION")
                    continue
                if decision not in ("ACCEPTED", "CAPACITY_FULL", "INSUFFICIENT_CASH", "SYMBOL_ALREADY_HELD"):
                    raise ValueError("UNKNOWN_PRIORITY_DECISION")
                outcome = row.get("historical_net_return_pct_outcome_not_selection_input")
                if not isinstance(outcome, (int, float)) or isinstance(outcome, bool):
                    raise ValueError("MISSING_HISTORICAL_OUTCOME")
                groups[decision].append(float(outcome))
                competition_days[row["entry_day"]].append((decision, float(outcome)))
            competing = [
                day for day, candidates in competition_days.items()
                if any(d == "ACCEPTED" for d, _ in candidates)
                and any(d == "CAPACITY_FULL" for d, _ in candidates)
            ]
            output[cohort][mode] = {
                "by_decision": {
                    reason: {"n": len(values),
                             "mean_historical_net_return_pct": round(sum(values)/len(values), 4) if values else None}
                    for reason, values in sorted(groups.items())
                },
                "entry_days_with_simultaneous_accepted_and_capacity_rejected": len(competing),
                "candidate_events_n": sum(map(len, groups.values())),
                "historical_outcomes_used_for_descriptive_audit_only": True,
                "simultaneous_comparison_not_causal_or_executable": True,
                "independent_predictive_validation": False,
                "trade_ready": False
            }
    return {"status": "DESCRIPTIVE_ONLY", "trade_ready": False,
            "analysis": output,
            "limitations": [
                "Rejected trades were not executed; historical outcomes are counterfactual.",
                "Mean returns do not establish paired replacement or portfolio profit.",
                "Overlapping candidates, correlated stocks and opportunity costs are not controlled.",
                "Previously inspected historical sample; no independent prospective validation."
            ]}


def main():
    source = Path("reports/candidate_feature_oos.json")
    report = json.loads(source.read_text(encoding="utf-8"))
    result = {pattern: summarize_capacity_opportunities(portfolio)
              for pattern, portfolio in report["portfolio_oos"].items()}
    dest = Path("reports/candidate_capacity_opportunity_audit.json")
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps({"status": "DESCRIPTIVE_ONLY", "patterns": sorted(result)}))


if __name__ == "__main__":
    main()
