"""Bounded European Yahoo daily OHLCV connectivity and metadata probe; research only."""
import json, math, time, urllib.error, urllib.parse, urllib.request
from datetime import datetime, timezone
from pathlib import Path

TESTS = [
    ("ASML.AS", "Amsterdam", "EUR"),
    ("SAP.DE", "Xetra", "EUR"),
    ("MC.PA", "Paris", "EUR"),
    ("NOVO-B.CO", "Copenhagen", "DKK"),
    ("AZN.L", "London", "GBp"),
    ("NESN.SW", "Zurich", "CHF"),
]
OUT = Path("reports/europe_data_probe.json")
OUT.parent.mkdir(exist_ok=True)

def probe(symbol, venue, expected_currency):
    url = "https://query1.finance.yahoo.com/v8/finance/chart/" + urllib.parse.quote(symbol, safe="") + "?range=1y&interval=1d"
    item = {"symbol":symbol,"venue_expected":venue,"currency_expected":expected_currency,
            "status":"DATA-BLOCKED","valid_bars":0}
    for attempt in range(1, 4):
        try:
            req=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0 DIPSAUS-research-probe","Accept":"application/json"})
            with urllib.request.urlopen(req,timeout=22) as response:
                payload=json.load(response)
            result=(payload.get("chart",{}).get("result") or [None])[0]
            if not result:
                raise ValueError(str(payload.get("chart",{}).get("error")))
            meta=result.get("meta") or {}
            item.update(currency_reported=meta.get("currency"),exchange_reported=meta.get("exchangeName"),
                        instrument_reported=meta.get("symbol"),timezone_reported=meta.get("exchangeTimezoneName"))
            quotes=((result.get("indicators") or {}).get("quote") or [{}])[0]
            timestamps=result.get("timestamp") or []
            bars=[]
            for i,ts in enumerate(timestamps):
                try:
                    o,h,l,c,v=(quotes[k][i] for k in ("open","high","low","close","volume"))
                    if not all(isinstance(x,(int,float)) and math.isfinite(x) for x in (o,h,l,c,v)):
                        continue
                    if l<=0 or l>min(o,c) or max(o,c)>h or v<0:
                        continue
                    bars.append(datetime.fromtimestamp(ts,timezone.utc).date().isoformat())
                except (IndexError,KeyError,TypeError):
                    continue
            item.update(valid_bars=len(bars),last_bar_date=max(bars) if bars else None,
                        first_bar_date=min(bars) if bars else None)
            # Yahoo London shares commonly report GBp/GBX; do not silently treat as GBP.
            actual=(meta.get("currency") or "").upper()
            accepted={"GBP","GBX","GBPENCE","GBP PENCE","GBPENNY","GBp".upper()} if symbol.endswith(".L") else {expected_currency.upper()}
            item["currency_matches_expectation"]=actual in accepted
            item["status"]="PASS" if len(bars)>=150 and item["currency_matches_expectation"] and meta.get("symbol")==symbol else "DATA-BLOCKED"
            if item["status"]!="PASS":
                item["reason"]="Insufficient bars, symbol mismatch or unexpected currency"
            break
        except (urllib.error.URLError,TimeoutError,ValueError,KeyError,TypeError,json.JSONDecodeError) as exc:
            item["reason"]=type(exc).__name__
            if attempt<3: time.sleep(attempt)
    return item

def main():
    results=[probe(*test) for test in TESTS]
    report={"generated_utc":datetime.now(timezone.utc).isoformat(),"scope":"Six named European symbols only; not a European market scan",
            "source":"Yahoo chart daily unadjusted OHLCV","research_only":True,
            "passed":sum(x["status"]=="PASS" for x in results),"tested":len(results),"results":results}
    OUT.write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding="utf-8")
    print(json.dumps(report,indent=2,ensure_ascii=False))
    if report["passed"]<4:
        raise SystemExit("European OHLCV probe failed minimum 4/6; inspect uploaded report")
if __name__=="__main__":
    main()

