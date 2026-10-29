#!/usr/bin/env python3
"""Research-only candidate snapshot; never a buy signal or an order."""
import json, math, os, statistics, urllib.parse, urllib.request
from datetime import datetime, timezone
from pathlib import Path

SYMBOLS = ("COHU", "BKD", "AMD", "PLTR", "AMZN", "RHM.DE")
CHART = "https://query1.finance.yahoo.com/v8/finance/chart/"
OUT = Path("reports/candidate_entry_research.json")
HEADERS = {"User-Agent": "Mozilla/5.0 DIPSAUS research"}

def bars(symbol):
    url = CHART + urllib.parse.quote(symbol, safe="") + "?range=1y&interval=1d"
    with urllib.request.urlopen(urllib.request.Request(url, headers=HEADERS), timeout=20) as response:
        result = json.load(response)["chart"]["result"][0]
    quote = result["indicators"]["quote"][0]
    rows = []
    for i, stamp in enumerate(result["timestamp"]):
        try:
            c, h, l, v = (quote[k][i] for k in ("close", "high", "low", "volume"))
            if any(x is None or not math.isfinite(float(x)) for x in (c, h, l, v)): continue
            if min(c, h, l) <= 0 or v < 0: continue
            rows.append({"timestamp": stamp, "close": float(c), "high": float(h), "low": float(l), "volume": int(v)})
        except (IndexError, TypeError, ValueError): continue
    return rows

def analyze(symbol, rows):
    result = {"symbol": symbol, "data_asof_utc": datetime.now(timezone.utc).isoformat(),
              "trade_ready": False, "decision": "WAIT", "source": "Yahoo daily unadjusted chart; research only"}
    if len(rows) < 80:
        result["blocks"] = ["INSUFFICIENT_DAILY_BARS"]; return result
    last = rows[-1]
    close = last["close"]
    previous = rows[-21:-1]
    highs = [r["high"] for r in previous]
    lows = [r["low"] for r in previous]
    volumes = [r["volume"] for r in previous]
    resistance = max(highs)
    support = min(lows)
    ma20 = statistics.mean(r["close"] for r in rows[-20:])
    ma50 = statistics.mean(r["close"] for r in rows[-50:])
    daily_changes = [(rows[i]["close"] / rows[i-1]["close"] - 1) for i in range(1, len(rows))]
    future = {}
    # Historical unconditional holding-window distribution: descriptive baseline, NOT strategy win rate.
    for horizon in (5, 10, 15):
        samples = [rows[i+horizon]["close"] / rows[i]["close"] - 1 for i in range(len(rows)-horizon)]
        future[str(horizon)] = {"n": len(samples), "median_return_pct": round(statistics.median(samples)*100, 2),
                                 "positive_fraction": round(sum(x>0 for x in samples)/len(samples), 3)}
    result.update(last_bar_utc=datetime.fromtimestamp(last["timestamp"], timezone.utc).isoformat(),
                  last_close=round(close, 4), ma20=round(ma20, 4), ma50=round(ma50, 4),
                  prior_20d_high=round(resistance, 4), prior_20d_low=round(support, 4),
                  volume_vs_prior_20d=round(last["volume"]/statistics.mean(volumes), 3) if statistics.mean(volumes) else None,
                  above_ma20=close>ma20, above_ma50=close>ma50,
                  twenty_day_breakout=close>resistance,
                  historical_unconditional_windows=future)
    result["blocks"] = ["DEGIRO_BID_ASK_UNVERIFIED", "EVENT_CALENDAR_UNVERIFIED",
                        "HISTORICAL_SIGNAL_COHORT_NOT_VALIDATED", "BROKER_FEES_FX_UNVERIFIED",
                        "RESISTANCE_AND_MANUAL_INVALIDATION_NOT_CLEARED", "RISK_REWARD_NOT_VALIDATED"]
    return result

def main():
    output = {"generated_utc": datetime.now(timezone.utc).isoformat(), "research_only": True, "candidates": []}
    for symbol in SYMBOLS:
        try: output["candidates"].append(analyze(symbol, bars(symbol)))
        except Exception as exc:
            output["candidates"].append({"symbol": symbol, "trade_ready": False, "decision": "DATA_BLOCKED",
                                         "error_type": type(exc).__name__, "blocks": ["PRICE_DATA_UNAVAILABLE"]})
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(output, indent=2), encoding="utf-8")
    print(json.dumps({"generated_utc": output["generated_utc"], "statuses":
                      {r["symbol"]: r["decision"] for r in output["candidates"]}}, indent=2))

if __name__ == "__main__": main()
