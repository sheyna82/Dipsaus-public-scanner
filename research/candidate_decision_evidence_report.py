"""Map existing descriptive ablation artifacts to conservative evidence-gate reports.

Descriptive historical medians are NOT calibrated probabilities or forecasts.
"""
import json
from pathlib import Path
from candidate_decision_evidence_gate import assess

def build(source):
    if not isinstance(source, dict) or not isinstance(source.get("candidates"), list):
        raise ValueError("INVALID_ABLATION_ARTIFACT")
    rows = []
    for candidate in source["candidates"]:
        symbol = candidate.get("symbol")
        if not symbol:
            raise ValueError("MISSING_SYMBOL")
        patterns = candidate.get("patterns", {})
        if not isinstance(patterns, dict):
            patterns = {}
        for pattern, result in patterns.items():
            if not isinstance(result, dict):
                continue
            cohorts = result.get("cohorts", {})
            if not isinstance(cohorts, dict):
                continue
            for filter_name, stats in cohorts.items():
                if not isinstance(stats, dict):
                    continue
                row = assess({"symbol": symbol})
                row.update({"pattern": pattern, "filter": filter_name,
                            "descriptive_test_n": stats.get("n"),
                            "descriptive_median_excess_pct": stats.get("median_excess_pct"),
                            "descriptive_median_mae_pct": stats.get("median_mae_pct"),
                            "descriptive_only": True})
                rows.append(row)
    return {"research_only": True, "trade_ready": False,
            "source": "candidate_feature_ablation.json",
            "warning": "Held-out descriptive results are not independent prospective validation.",
            "candidates": rows}

def main():
    source = Path("reports/candidate_feature_ablation.json")
    if not source.is_file():
        raise FileNotFoundError("ABLATION_ARTIFACT_MISSING")
    result = build(json.loads(source.read_text(encoding="utf-8")))
    target = Path("reports/candidate_decision_evidence.json")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps({"status": "RESEARCH_ONLY", "rows": len(result["candidates"])}))

if __name__ == "__main__":
    main()
