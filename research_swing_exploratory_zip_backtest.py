"""Exploratory offline comparison of four fixed swing rules on an Actions ZIP.

Run: python research_swing_exploratory_zip_backtest.py downloaded-prices.zip
No downloading, trading, tuning, source authentication, or production writes.
Returns are research proxies; results are not an independently validated edge.
"""
import json
import statistics
import sys
import zipfile

HORIZONS = (3, 5, 10, 20)
RULES = ("momentum_20d", "recovery_5d", "breakout_20d", "pullback_5d")

def compare_archive(path, *, cost_bps=30, step=20):
    if not 0 <= cost_bps <= 1000 or type(step) is not int or step < 20:
        raise ValueError("invalid_assumptions")
    with zipfile.ZipFile(path) as archive:
        coverage = json.loads(archive.read("coverage.json"))
        symbols = [x["symbol"] for x in coverage["manifest"]["symbols"]]
        benchmarks = ["SPY", "IWM"]
        bars = {s: json.loads(archive.read(s + ".json"))["rows"] for s in symbols + benchmarks}
    dates = {tuple(r["timestamp"] for r in rows) for rows in bars.values()}
    if len(dates) != 1 or len(next(iter(dates))) < 80:
        raise ValueError("unaligned_or_insufficient_panel")
    n = len(bars["SPY"])
    results = []
    for horizon in HORIZONS:
        for rule in RULES:
            cohort_returns, spy_excess, iwm_excess = [], [], []
            for t in range(40, n - horizon, step):
                scored = []
                for symbol in symbols:
                    rows = bars[symbol]
                    close = rows[t]["close"]
                    r20 = close / rows[t - 20]["close"] - 1
                    r5 = close / rows[t - 5]["close"] - 1
                    near_high = close / max(r["high"] for r in rows[t - 19:t + 1]) - 1
                    score = {"momentum_20d": r20, "recovery_5d": -r5,
                             "breakout_20d": near_high,
                             "pullback_5d": -r5 if r20 > 0 and r5 < 0 else -999}[rule]
                    if score > -999:
                        scored.append((score, symbol))
                selected = sorted(scored, reverse=True)[:6]
                if not selected:
                    continue
                # Six equal capital slots; unused slots remain cash at zero return.
                net = sum(100 * (bars[s][t + horizon]["close"] /
                                 bars[s][t + 1]["open"] - 1) - cost_bps / 100
                          for _, s in selected) / 6
                cohort_returns.append(net)
                for benchmark, target in (("SPY", spy_excess), ("IWM", iwm_excess)):
                    benchmark_net = (100 * (bars[benchmark][t + horizon]["close"] /
                                           bars[benchmark][t + 1]["open"] - 1)
                                     - cost_bps / 100)
                    target.append(net - benchmark_net)
            if cohort_returns:
                results.append({"horizon": horizon, "rule": rule,
                                "cohorts": len(cohort_returns),
                                "mean_net_pct": round(statistics.mean(cohort_returns), 4),
                                "median_net_pct": round(statistics.median(cohort_returns), 4),
                                "positive_fraction": round(sum(x > 0 for x in cohort_returns) /
                                                           len(cohort_returns), 4),
                                "mean_excess_spy_pp": round(statistics.mean(spy_excess), 4),
                                "mean_excess_iwm_pp": round(statistics.mean(iwm_excess), 4),
                                "worst_cohort_pct": round(min(cohort_returns), 4)})
    return {"research_only": True, "trade_ready": False, "edge_proven": False,
            "source_authenticity_verified": False, "cost_bps": cost_bps,
            "cohort_step_sessions": step, "results": results}

if __name__ == "__main__":
    print(json.dumps(compare_archive(sys.argv[1]), indent=2))
