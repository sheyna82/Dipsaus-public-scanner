"""Point-in-time daily OHLCV replay. Research, not executable broker signals.

Entry at NEXT day's open after signal at close. Stops checked against subsequent
daily low, with gap-through stop filled at next open. No same-bar target optimism:
stop wins when both stop and target are touched. EUR listings only for P&L.
"""
import json, math
from datetime import datetime, timezone
from pathlib import Path
import yfinance as yf
from risk_budget_plan import build_trade_plan

WATCH = {"FER.MC": "Ferrovial (Madrid, EUR)",
         "RHM.DE": "Rheinmetall (Xetra, EUR)",
         "GEHC": "GE HealthCare (NASDAQ, USD)"}


def fetch(ticker):
    df = yf.Ticker(ticker).history(period="2y", interval="1d", auto_adjust=False)
    if df.empty or len(df) < 100:
        raise RuntimeError("DATA-BLOCKED: insufficient market history")
    return [{"date": str(idx.date()), "open": float(r["Open"]),
             "high": float(r["High"]), "low": float(r["Low"]),
             "close": float(r["Close"])} for idx, r in df.iterrows()
            if all(math.isfinite(float(r[k])) and float(r[k]) > 0
                   for k in ("Open", "High", "Low", "Close"))]


def replay(rows, *, currency="EUR"):
    events = []
    blocked = []
    if currency != "EUR":
        return {"status": "FX-BLOCKED", "trades": [], "reason": "Verified historical FX required"}
    for i in range(30, len(rows) - 11):
        past = rows[:i+1]
        closes = [r["close"] for r in past]
        lows = [r["low"] for r in past]
        signal = (closes[-1] > sum(closes[-5:])/5 and
                  sum(closes[-5:])/5 > sum(closes[-10:-5])/5 and
                  closes[-1] >= min(lows[-20:])*1.03 and
                  min(lows[-5:]) > min(lows[-20:-5]))
        if not signal:
            continue
        # Next-session open; no future data used for stop or target.
        entry = rows[i+1]["open"]
        stop = min(lows[-10:]) * 0.995
        if stop >= entry:
            continue
        target = entry + 3*(entry-stop)
        plan = build_trade_plan(entry, stop, target, verified=False)
        if plan.shares < 1 or plan.potential_profit < 150:
            blocked.append(rows[i]["date"])
            continue
        # Non-overlapping 10-session horizon; track each outcome independently.
        exit_price = rows[min(i+10, len(rows)-1)]["close"]
        exit_date = rows[min(i+10, len(rows)-1)]["date"]
        reason = "TIME_EXIT"
        for day in rows[i+1:i+11]:
            if day["open"] <= stop:
                exit_price, exit_date, reason = day["open"], day["date"], "STOP_GAP"
                break
            if day["low"] <= stop:
                exit_price, exit_date, reason = stop, day["date"], "STOP"
                break
            if day["high"] >= target:
                exit_price, exit_date, reason = target, day["date"], "TARGET"
                break
        events.append({"signal_date": rows[i]["date"], "entry_date": rows[i+1]["date"],
                       "exit_date": exit_date, "entry": round(entry, 4),
                       "stop": round(stop, 4), "target": round(target, 4),
                       "shares": plan.shares, "exit": round(exit_price, 4),
                       "exit_reason": reason,
                       "gross_eur": round((exit_price-entry)*plan.shares, 2)})
    # Signals overlap; DO NOT interpret the sum as a portfolio equity curve.
    return {"status": "RESEARCH_ONLY", "overlapping_signals": True,
            "trades": events, "rejected_profit_or_size": len(blocked),
            "gross_eur_sum_not_portfolio_pnl": round(sum(x["gross_eur"] for x in events), 2),
            "limitations": ["Overlapping candidate trades", "No fees, spread or slippage beyond stop gaps",
                            "No earnings/news or broker validation", "Daily candles cannot resolve intraday ordering",
                            "Uncalibrated rule set; selection and survivorship bias"]}


def main():
    result = {"generated_utc": datetime.now(timezone.utc).isoformat(),
              "type": "HISTORICAL_RESEARCH_NOT_LIVE_ADVICE", "symbols": {}}
    for symbol, name in WATCH.items():
        try:
            rows = fetch(symbol)
            currency = "USD" if symbol == "GEHC" else "EUR"
            result["symbols"][symbol] = {"name": name, "bars": len(rows),
                                         "first_date": rows[0]["date"], "last_date": rows[-1]["date"],
                                         "replay": replay(rows, currency=currency)}
        except Exception as exc:
            result["symbols"][symbol] = {"status": "DATA-BLOCKED",
                                          "error": type(exc).__name__ + ": " + str(exc)[:180]}
    Path("historical_replay_report.json").write_text(json.dumps(result, indent=2))
    print(json.dumps({k: {"status": v.get("replay", v).get("status"),
                          "signals": len(v.get("replay", {}).get("trades", []))}
                      for k,v in result["symbols"].items()}, indent=2))
    if all(v.get("status") == "DATA-BLOCKED" for v in result["symbols"].values()):
        raise SystemExit("No usable history from provider")


if __name__ == "__main__":
    main()
