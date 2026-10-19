"""Historical research comparison; no brokerage orders or notifications."""
from historical_replay import fetch
from risk_budget_plan import build_trade_plan
import json

def simulate(bars, protection=False, currency="EUR", horizon=10, target_r=3.0):
    trades = []
    index = 30
    while index < len(bars) - horizon - 2:
        history = bars[:index+1]
        closes = [bar["close"] for bar in history]
        lows = [bar["low"] for bar in history]
        average5 = sum(closes[-5:]) / 5
        prior5 = sum(closes[-10:-5]) / 5
        signal = (closes[-1] > average5 > prior5
                  and closes[-1] >= min(lows[-20:]) * 1.03
                  and min(lows[-5:]) > min(lows[-20:-5]))
        if not signal:
            index += 1
            continue
        entry = bars[index+1]["open"] * 1.001
        stop = min(lows[-10:]) * 0.995
        if stop >= entry:
            index += 1
            continue
        target = entry + target_r * (entry-stop)
        plan = build_trade_plan(entry, stop, target)
        if not plan.shares or plan.potential_profit < 150:
            index += 1
            continue
        peak = entry
        end = index + horizon
        sale = bars[end]["close"] * 0.999
        reason = "TIME"
        for day_index in range(index+1, end+1):
            day = bars[day_index]
            if day["open"] <= stop:
                sale, end, reason = day["open"] * 0.999, day_index, "GAP"
                break
            if day["low"] <= stop:
                sale, end, reason = stop * 0.999, day_index, "STOP"
                break
            if day["high"] >= target:
                sale, end, reason = target * 0.999, day_index, "TARGET"
                break
            peak = max(peak, day["close"])
            if (protection and day_index > index+1
                    and peak-entry >= entry-stop
                    and day["close"] <= peak - 0.35*(peak-entry)):
                sale, end, reason = bars[day_index+1]["open"] * 0.999, day_index+1, "GIVEBACK_NEXT_OPEN"
                break
        trades.append({"entry_date": bars[index+1]["date"],
                       "exit_date": bars[end]["date"],
                       "net_native": round((sale-entry)*plan.shares-4, 2),
                       "exit_reason": reason})
        index = end+1
    return {"trades": trades, "count": len(trades), "currency": currency,
            "net_native": round(sum(t["net_native"] for t in trades), 2),
            "wins": sum(t["net_native"] > 0 for t in trades)}

def diagnostics(trades):
    from collections import Counter
    balance = high = max_drawdown = 0.0
    for trade in trades:
        balance += trade["net_native"]
        high = max(high, balance)
        max_drawdown = max(max_drawdown, high - balance)
    positives = sum(t["net_native"] for t in trades if t["net_native"] > 0)
    negatives = -sum(t["net_native"] for t in trades if t["net_native"] < 0)
    return {"trades": len(trades),
            "wins": sum(t["net_native"] > 0 for t in trades),
            "profit_factor": round(positives / negatives, 3) if negatives else None,
            "max_closed_trade_drawdown_native": round(max_drawdown, 2),
            "exit_reasons": dict(Counter(t["exit_reason"] for t in trades)),
            "worst_five": sorted(trades, key=lambda t: t["net_native"])[:5]}

def main():
    report = {"research_only": True, "assumptions":
              {"fee_per_order_eur": 2, "slippage_fraction": 0.001,
               "single_position": True, "horizon_sessions": 10},
              "limitations": ["Synthetic rules, not user's historical orders",
                              "Daily close protection proxy, not live structure engine",
                              "USD results are in USD, EUR in EUR; no FX conversion or combined portfolio P&L",
                              "Nominal risk budget 75 in native currency, not comparable cross-currency",
                              "No news or intraday sequence verification"],
              "symbols": {}}
    # Broad market research universe; no personal holdings or trade records.
    universe = {"FER.MC":"EUR", "RHM.DE":"EUR", "BESI.AS":"EUR",
                "HWM":"USD", "FCX":"USD", "GEV":"USD", "AMD":"USD",
                "COHR":"USD", "KLAC":"USD", "LRCX":"USD",
                "TSLA":"USD", "VRT":"USD", "HEI":"USD"}
    for ticker, currency in universe.items():
        try:
            bars = fetch(ticker)
            report["symbols"][ticker] = {
                "currency": currency,
                "baseline": simulate(bars, currency=currency),
                "profit_protection": simulate(bars, True, currency=currency),
                "first_date": bars[0]["date"],
                "last_date": bars[-1]["date"]}
        except Exception as error:
            report["symbols"][ticker] = {"status": "DATA-BLOCKED",
                                          "reason": str(error)[:160]}

    for ticker, item in report["symbols"].items():
        if "baseline" not in item:
            continue
        item["diagnostics"] = {
            name: diagnostics(item[name]["trades"])
            for name in ("baseline", "profit_protection")}
        baseline = {t["entry_date"]: t for t in item["baseline"]["trades"]}
        protected = {t["entry_date"]: t for t in item["profit_protection"]["trades"]}
        common = set(baseline) & set(protected)
        item["paired_same_entry"] = {
            "count": len(common),
            "net_difference_native": round(sum(
                protected[date]["net_native"] - baseline[date]["net_native"]
                for date in common), 2),
            "changed_exits": sum(
                protected[date]["exit_date"] != baseline[date]["exit_date"]
                for date in common)}
    # Independent exit-rule sensitivity grid. Research only: same synthetic signal.
    # Protection executes next session open after a completed daily close.
    for ticker, item in report["symbols"].items():
        if "baseline" not in item:
            continue
        bars = fetch(ticker)
        item["sensitivity"] = {}
        for horizon in (10, 15, 20):
            for target_r in (2.0, 2.5, 3.0):
                key = f"h{horizon}_r{target_r:g}"
                item["sensitivity"][key] = {}
                for protection, mode in ((False, "baseline"), (True, "protection_next_open")):
                    run = simulate(bars, protection, item["currency"], horizon, target_r)
                    item["sensitivity"][key][mode] = {
                        "count": run["count"], "net_native": run["net_native"],
                        "profit_factor": diagnostics(run["trades"])["profit_factor"],
                        "stop_or_gap": sum(t["exit_reason"] in ("STOP", "GAP") for t in run["trades"])}
    report["limitations"].append("Sensitivity grid is in-sample; choose no live parameters without out-of-sample validation")
    report["limitations"].append("Baseline stop/target are simulated intraday orders, not user's actual limit-only execution")
    report["assumptions"]["protection_execution"] = "next session open after confirmed close"
    # Chronological holdout: train on earlier 70%, evaluate untouched final 30%.
    # Warm-up bars before split are indicators only; first holdout entry is at split.
    for ticker, item in report["symbols"].items():
        if "baseline" not in item:
            continue
        bars = fetch(ticker)
        split = int(len(bars) * 0.7)
        if split < 50 or len(bars) - split < 30:
            item["holdout"] = {"status": "INSUFFICIENT_DATA"}
            continue
        train = bars[:split]
        test = bars[split - 31:]
        candidates = []
        for horizon in (10, 15, 20):
            for target_r in (2.0, 2.5, 3.0):
                for protect in (False, True):
                    result = simulate(train, protect, item["currency"], horizon, target_r)
                    if result["count"] >= 5:
                        candidates.append((result["net_native"], horizon, target_r, protect, result["count"]))
        if not candidates:
            item["holdout"] = {"status": "INSUFFICIENT_TRAIN_TRADES"}
            continue
        # Select ONLY on training data, never on holdout.
        best = max(candidates, key=lambda x: x[0])
        _, horizon, target_r, protect, train_count = best
        hold = simulate(test, protect, item["currency"], horizon, target_r)
        fixed = simulate(test, False, item["currency"], 10, 3.0)
        item["holdout"] = {
            "train_last_date": train[-1]["date"],
            "test_first_entry_date": test[31]["date"],
            "test_last_date": test[-1]["date"],
            "selection": {"horizon": horizon, "target_r": target_r,
                          "protection_next_open": protect,
                          "train_count": train_count, "train_net_native": best[0]},
            "selected_test": {"count": hold["count"], "net_native": hold["net_native"],
                              "profit_factor": diagnostics(hold["trades"])["profit_factor"]},
            "fixed_baseline_test": {"count": fixed["count"], "net_native": fixed["net_native"],
                                    "profit_factor": diagnostics(fixed["trades"])["profit_factor"]}}
    report["limitations"].append("Holdout split is chronological 70/30, but the 13-symbol universe and candidate grid were chosen after prior exploratory analysis")
    report["limitations"].append("Train/test sample sizes can be small; no statistical confidence or independent market-regime replication")
    print(json.dumps({ticker: item.get("holdout", {}) for ticker, item in report["symbols"].items()}, indent=2))
    with open("historical_comparison_report.json", "w") as output:
        json.dump(report, output, indent=2)
    print(json.dumps({ticker: {
        mode: {"count": data[mode]["count"], "net_native": data[mode]["net_native"], "currency": data[mode]["currency"]}
        for mode in ("baseline", "profit_protection") if mode in data}
        for ticker, data in report["symbols"].items()}, indent=2))

if __name__ == "__main__":
    main()
