"""Historical research comparison; no brokerage orders or notifications."""
from historical_replay import fetch
from risk_budget_plan import build_trade_plan
import json

def simulate(bars, protection=False, currency="EUR"):
    trades = []
    index = 30
    while index < len(bars) - 11:
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
        target = entry + 3 * (entry-stop)
        plan = build_trade_plan(entry, stop, target)
        if not plan.shares or plan.potential_profit < 150:
            index += 1
            continue
        peak = entry
        end = index + 10
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
                sale, end, reason = day["close"] * 0.999, day_index, "GIVEBACK"
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
    with open("historical_comparison_report.json", "w") as output:
        json.dump(report, output, indent=2)
    print(json.dumps({ticker: {
        mode: {"count": data[mode]["count"], "net_native": data[mode]["net_native"], "currency": data[mode]["currency"]}
        for mode in ("baseline", "profit_protection") if mode in data}
        for ticker, data in report["symbols"].items()}, indent=2))

if __name__ == "__main__":
    main()
