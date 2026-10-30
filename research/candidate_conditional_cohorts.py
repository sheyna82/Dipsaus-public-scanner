"""Offline, point-in-time conditional research. No trading signals or orders."""
import json, math, statistics
from pathlib import Path
from candidate_entry_snapshot import SYMBOLS, bars

HORIZONS = (5, 10, 15)

def cohort(rows, horizon, lookback=20):
    """Only past bars define entry; future bars used strictly for evaluation."""
    samples = []
    for i in range(max(50, lookback), len(rows)-horizon):
        past = rows[i-lookback:i]
        entry = rows[i]["close"]
        if entry <= 0: continue
        ma20 = statistics.mean(r["close"] for r in rows[i-19:i+1])
        ma50 = statistics.mean(r["close"] for r in rows[i-49:i+1])
        prior_high = max(r["high"] for r in past)
        prior_low = min(r["low"] for r in past)
        # These are distinct research hypotheses, not an optimized production signal.
        conditions = {
            "all_days": True,
            "above_ma20_below_ma50": entry > ma20 and entry < ma50,
            "above_both_mas": entry > ma20 and entry > ma50,
            "breakout_prior20": entry > prior_high,
            "recovery_from_prior20_low_3to15pct": 1.03 <= entry/prior_low <= 1.15,
        }
        future = rows[i+1:i+horizon+1]
        exit_return = future[-1]["close"]/entry-1
        adverse = min(x["low"]/entry-1 for x in future)
        favorable = max(x["high"]/entry-1 for x in future)
        for name, ok in conditions.items():
            if ok: samples.append((name, i, exit_return, adverse, favorable))
    output = {}
    for name in ("all_days", "above_ma20_below_ma50", "above_both_mas", "breakout_prior20", "recovery_from_prior20_low_3to15pct"):
        subset = [x for x in samples if x[0] == name]
        if not subset:
            output[name] = {"n": 0, "eligible": False}
            continue
        returns = [x[2] for x in subset]
        maes = [x[3] for x in subset]
        mfes = [x[4] for x in subset]
        output[name] = {
            "n": len(subset), "eligible": len(subset) >= 30,
            "median_return_pct": round(100*statistics.median(returns), 2),
            "positive_fraction": round(sum(x>0 for x in returns)/len(returns), 3),
            "median_mae_pct": round(100*statistics.median(maes), 2),
            "worst_mae_pct": round(100*min(maes), 2),
            "median_mfe_pct": round(100*statistics.median(mfes), 2),
            "overlapping_windows": True,
        }
    return output

def main():
    result = {"research_only": True, "trade_ready": False,
              "limitations": ["One year per symbol, overlapping forward windows, unadjusted Yahoo daily bars",
                              "No event matching, fees, FX, bid-ask, benchmark, or out-of-sample validation",
                              "n>=30 is descriptive only, not evidence of robust predictive edge"],
              "candidates": []}
    for symbol in SYMBOLS:
        try:
            rows = bars(symbol)
            if len(rows) < 80: raise ValueError("INSUFFICIENT_BARS")
            result["candidates"].append({"symbol": symbol, "bars": len(rows), "trade_ready": False,
                                         "horizons": {str(h): cohort(rows, h) for h in HORIZONS}})
        except Exception as exc:
            result["candidates"].append({"symbol": symbol, "trade_ready": False,
                                         "status": "DATA_BLOCKED", "error_type": type(exc).__name__})
    output = Path("reports/candidate_conditional_cohorts.json")
    output.parent.mkdir(exist_ok=True, parents=True)
    output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps({"candidate_statuses": {x["symbol"]: x.get("status", "RESEARCH_ONLY") for x in result["candidates"]}}))

if __name__ == "__main__": main()
