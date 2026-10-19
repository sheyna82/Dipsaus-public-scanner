"""Historical research comparison; no brokerage orders or notifications."""
from historical_replay import fetch
from risk_budget_plan import build_trade_plan
import json

def simulate(bars, protection=False):
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
                       "net_eur": round((sale-entry)*plan.shares-4, 2),
                       "exit_reason": reason})
        index = end+1
    return {"trades": trades, "count": len(trades),
            "net_eur": round(sum(t["net_eur"] for t in trades), 2),
            "wins": sum(t["net_eur"] > 0 for t in trades)}

def main():
    report = {"research_only": True, "assumptions":
              {"fee_per_order_eur": 2, "slippage_fraction": 0.001,
               "single_position": True, "horizon_sessions": 10},
              "limitations": ["Synthetic rules, not user's historical orders",
                              "Daily close protection proxy, not live structure engine",
                              "No FX, news or intraday sequence verification"],
              "symbols": {}}
    for ticker in ("FER.MC", "RHM.DE"):
        try:
            bars = fetch(ticker)
            report["symbols"][ticker] = {
                "baseline": simulate(bars),
                "profit_protection": simulate(bars, True),
                "first_date": bars[0]["date"],
                "last_date": bars[-1]["date"]}
        except Exception as error:
            report["symbols"][ticker] = {"status": "DATA-BLOCKED",
                                          "reason": str(error)[:160]}
    report["symbols"]["GEHC"] = {"status": "FX-BLOCKED"}
    with open("historical_comparison_report.json", "w") as output:
        json.dump(report, output, indent=2)
    print(json.dumps({ticker: {
        mode: {"count": data[mode]["count"], "net_eur": data[mode]["net_eur"]}
        for mode in ("baseline", "profit_protection") if mode in data}
        for ticker, data in report["symbols"].items()}, indent=2))

if __name__ == "__main__":
    main()
