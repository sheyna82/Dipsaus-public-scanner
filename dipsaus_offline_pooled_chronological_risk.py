"""Pool already reported chronological cohorts without claiming independence.

Ticker-level test sufficiency remains mandatory; a pooled count never
converts four underpowered ticker tests into independent validation.
"""
def summarize_chronological_cohorts(results):
    if not isinstance(results, (list, tuple)) or not results:
        return {"status": "DATA_BLOCKED", "reason": "missing_results"}
    output = {"train": {"events": 0, "excess_weighted": 0., "adverse_weighted": 0.},
              "test": {"events": 0, "excess_weighted": 0., "adverse_weighted": 0.}}
    tickers = []
    for r in results:
        if not isinstance(r, dict) or r.get("status") != "EXPLORATORY_COMBINED_RETURN_RISK":
            return {"status": "DATA_BLOCKED", "reason": "invalid_symbol"}
        d = r.get("chronological_diagnostic")
        if not isinstance(d, dict) or d.get("status") != "EXPLORATORY_CHRONOLOGICAL_DIAGNOSTIC":
            return {"status": "DATA_BLOCKED", "reason": "invalid_chronology"}
        tickers.append({"symbol": r["symbol"], "test_events": d["test"]["events"],
                        "ticker_test_sufficient": d["test_events_sufficient"]})
        for key in ("train", "test"):
            item = d[key]
            n = item["events"]
            if type(n) is not int or n < 0:
                return {"status": "DATA_BLOCKED", "reason": "invalid_count"}
            if n:
                from math import isfinite
                a, z = item["mean_excess_pct_points"], item["mean_extra_adverse_pct_points"]
                if type(a) not in (int, float) or type(z) not in (int, float) or not isfinite(a) or not isfinite(z):
                    return {"status": "DATA_BLOCKED", "reason": "invalid_metric"}
                output[key]["excess_weighted"] += n * a
                output[key]["adverse_weighted"] += n * z
            output[key]["events"] += n
    cohorts = {}
    for key, data in output.items():
        n = data["events"]
        cohorts[key] = {"events": n,
                        "mean_excess_pct_points": round(data["excess_weighted"] / n, 6) if n else None,
                        "mean_extra_adverse_pct_points": round(data["adverse_weighted"] / n, 6) if n else None}
    return {"status": "EXPLORATORY_POOLED_CHRONOLOGY", "cohorts": cohorts,
            "tickers": tickers, "all_tickers_sufficient": all(t["ticker_test_sufficient"] for t in tickers),
            "independent_untouched_holdout": False, "predictive_edge_proven": False,
            "trade_ready": False}
