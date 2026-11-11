"""Offline multi-ticker descriptive evaluation; no probability or trade signals."""
from dipsaus_offline_cohort_gate import cohort_eligibility
from dipsaus_offline_price_history_eval import evaluate_local_history


def evaluate_cohort(records, benchmark_path):
    gate = cohort_eligibility(records)
    if not gate["eligible"]:
        return {"status": "REJECTED", "reasons": gate["reasons"]}
    results = []
    for record in records:
        path = record.get("csv_path")
        if not isinstance(path, str) or not path:
            return {"status": "REJECTED", "reasons": ["missing_csv_path"]}
        outcome = evaluate_local_history(path, benchmark_path)
        if outcome["status"] != "EXPLORATORY_ONLY":
            return {"status": "REJECTED", "reasons": [
                f'{record["symbol"]}:{outcome.get("reason", "invalid_evaluation")}']}
        results.append({"symbol": record["symbol"], "observations": outcome["observations"],
                        "selected_count": outcome["selected_count"],
                        "selected_mean_net_pct": outcome["selected_mean_net_pct"],
                        "all_mean_net_pct": outcome["always_enter_mean_net_pct"]})
    return {"status": "EXPLORATORY_ONLY", "per_ticker": results,
            "tickers": len(results), "earnings_calendar_verified": False,
            "independent_holdout_verified": False,
            "provenance_independently_verified": False,
            "trade_ready": False,
            "limitations": "Descriptive per-ticker price-only comparisons; caller-attested provenance, no aggregate significance, no complete earnings calendar or untouched holdout."}
