"""Bounded Yahoo OHLCV reliability test; not a DIPSAUS scan or live-price feed."""
import json, time, urllib.error, urllib.parse, urllib.request
from datetime import datetime, timezone
from pathlib import Path

SYMBOLS = ["AAPL","MSFT","JNJ","XOM","JPM","CAT","WMT","PFE","BA","CVX",
           "KO","DIS","NKE","UNH","GS","FCX","GE","HD","AMD","T"]
OUT = Path("reports")
OUT.mkdir(exist_ok=True)
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; DipsausSourceAudit/0.3)"}

def probe(symbol):
    url = ("https://query1.finance.yahoo.com/v8/finance/chart/"
           + urllib.parse.quote(symbol, safe="")
           + "?range=1y&interval=1d")
    started = time.monotonic()
    try:
        with urllib.request.urlopen(urllib.request.Request(url,headers=HEADERS),timeout=18) as r:
            data = json.load(r)
        result = data["chart"]["result"][0]
        q = result["indicators"]["quote"][0]
        stamps = result["timestamp"]
        valid = [(t,c,v) for t,c,v in zip(stamps,q["close"],q["volume"])
                 if c is not None and v is not None]
        if len(valid) < 150:
            return {"symbol":symbol,"status":"insufficient_bars","valid_bars":len(valid),
                    "seconds":round(time.monotonic()-started,2)}
        return {"symbol":symbol,"status":"ok","valid_bars":len(valid),
                "last_bar_utc":datetime.fromtimestamp(valid[-1][0],timezone.utc).isoformat(),
                "seconds":round(time.monotonic()-started,2)}
    except urllib.error.HTTPError as e:
        return {"symbol":symbol,"status":"http_error","http_status":e.code,
                "seconds":round(time.monotonic()-started,2)}
    except Exception as e:
        return {"symbol":symbol,"status":"error","error_type":type(e).__name__,
                "seconds":round(time.monotonic()-started,2)}

def main():
    rows=[]
    for i,symbol in enumerate(SYMBOLS):
        if i:
            time.sleep(2)
        result=probe(symbol)
        rows.append(result)
        print(json.dumps(result),flush=True)
        if result.get("http_status") in (401,403,429):
            print("STOP: authorization/rate limit detected; no retry or evasion",flush=True)
            break
    good=sum(r["status"]=="ok" for r in rows)
    report={"run_utc":datetime.now(timezone.utc).isoformat(),
            "status":"BOUNDED_SOURCE_RELIABILITY_TEST","requested":len(SYMBOLS),
            "attempted":len(rows),"successful":good,"results":rows,
            "actual_symbols_screened_for_recovery":0,"full_us_scan_executed":False,
            "trade_ready":False,
            "limitations":"20 diverse symbols, one run; does not prove multi-thousand-symbol capacity, license, or live quote accuracy."}
    (OUT/"yahoo_reliability.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
    print(json.dumps({"attempted":len(rows),"successful":good,"report":"reports/yahoo_reliability.json"}),flush=True)
    if good!=len(SYMBOLS):
        raise SystemExit("Source reliability test incomplete; see artifact")

if __name__=="__main__":
    main()

