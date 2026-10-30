"""Research-only accepted-trade turnover diagnostic for existing ablation artifacts.

Usage: python research/candidate_trade_turnover_audit.py candidate_feature_ablation.json
No trading signals are generated; results are descriptive, not causal.
"""
import json
import math
import sys


def audit(report, pattern="recovery_from_prior20_low_3to15pct"):
    portfolios = report["portfolio_capacity_25bps"][pattern]["comparison"]
    baseline = portfolios["baseline"]["accepted_signals"]
    def index(rows):
        indexed = {}
        for row in rows:
            key = (row["symbol"], row["entry_day"], row["exit_day"])
            if key in indexed:
                raise ValueError("DUPLICATE_ACCEPTED_TRADE_IDENTITY")
            indexed[key] = row
        return indexed
    base = index(baseline)
    result = {"research_only": True, "trade_ready": False, "pattern": pattern,
              "limitations": [
                  "Differences are not matched randomized outcomes or causal filter effects",
                  "Different capacity competition changes accepted populations",
                  "No daily mark-to-market drawdown, verified fills or independent OOS test",
                  "A removed trade may not have been eligible under the alternative portfolio"
              ], "comparisons": {}}
    for name, portfolio in portfolios.items():
        other = index(portfolio["accepted_signals"])
        shared = base.keys() & other.keys()
        for key in shared:
            a = base[key]["net_return_pct"]
            b = other[key]["net_return_pct"]
            if not all(isinstance(v, (int, float)) and not isinstance(v, bool)
                       and math.isfinite(v) for v in (a, b)):
                raise ValueError("INVALID_SHARED_TRADE_RETURN")
            if not math.isclose(a, b, rel_tol=0, abs_tol=1e-8):
                raise ValueError("SHARED_TRADE_RETURN_MISMATCH")
        removed = base.keys() - other.keys()
        added = other.keys() - base.keys()
        def mean(rows):
            return (round(sum(float(row["net_return_pct"]) for row in rows) /
                          len(rows), 6) if rows else None)
        result["comparisons"][name] = {
            "baseline_accepted": len(base),
            "alternative_accepted": len(other),
            "shared_trade_identities": len(shared),
            "baseline_only": len(removed),
            "alternative_only": len(added),
            "baseline_only_mean_net_return_pct": mean([base[k] for k in removed]),
            "alternative_only_mean_net_return_pct": mean([other[k] for k in added]),
            "alternative_portfolio_return_pct": portfolio["realized_return_pct"],
            "baseline_portfolio_return_pct": portfolios["baseline"]["realized_return_pct"],
            "return_difference_percentage_points": round(
                portfolio["realized_return_pct"] -
                portfolios["baseline"]["realized_return_pct"], 4),
        }
    return result


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Usage: candidate_trade_turnover_audit.py <ablation.json>")
    with open(sys.argv[1], encoding="utf-8") as source:
        print(json.dumps(audit(json.load(source)), indent=2, sort_keys=True))
