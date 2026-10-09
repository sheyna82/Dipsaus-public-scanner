"""Bounded 60-symbol US historical-data database pilot. NOT trade signals."""
import csv, gzip, hashlib, json, re, time, urllib.error, urllib.parse, urllib.request
from datetime import datetime, timezone
from pathlib import Path
BASE=Path("reports");BASE.mkdir(exist_ok=True)
HEADERS={"User-Agent":"Mozilla/5.0 (compatible; DipsausDataPilot/0.1)"}
def get(url):
    with urllib.request.urlopen(urllib.request.Request(url,headers=HEADERS),timeout=25) as r:return r.read()
def universe():
    urls=["https://www.nasdaqtrader.com/dynamic/SymDir/nasdaqlisted.txt",
          "https://www.nasdaqtrader.com/dynamic/SymDir/otherlisted.txt"]
    found=[]
    for index,url in enumerate(urls):
        raw=get(url).decode("utf-8-sig")
        rows=csv.DictReader((line for line in raw.splitlines() if not line.startswith("File Creation Time")),delimiter="|")
        for r in rows:
            sym=r.get("Symbol" if index==0 else "ACT Symbol","").strip()
            name=r.get("Security Name","").lower()
            if r.get("Test Issue")!="N" or r.get("ETF")!="N":continue
            if not re.fullmatch(r"[A-Z]{1,5}",sym):continue
            if any(w in name for w in ("warrant","rights","unit "," units","preferred","depositary","etn","exchange traded","notes due","bond","debenture")):continue
            found.append(sym)
    return sorted(set(found))
def bars(symbol):
    url="https://query1.finance.yahoo.com/v8/finance/chart/"+urllib.parse.quote(symbol,safe="")+"?range=1y&interval=1d"
    result=json.loads(get(url))["chart"]["result"][0]
    q=result["indicators"]["quote"][0]
    records=[]
    for i,t in enumerate(result["timestamp"]):
        vals=[q[k][i] for k in ("open","high","low","close","volume")]
        if any(v is None for v in vals):continue
        records.append([datetime.fromtimestamp(t,timezone.utc).date().isoformat(),*vals])
    return records
def main():
    symbols=universe()
    # Deterministic, alphabetically distributed sample; avoids bias toward A-tickers.
    selected=sorted(symbols, key=lambda s: hashlib.sha256(s.encode()).hexdigest())[:60]
    stats={"started_utc":datetime.now(timezone.utc).isoformat(),"universe_preliminary":len(symbols),
           "requested":len(selected),"attempted":0,"stored":0,"failed":[],"insufficient_history":[],
           "symbols_screened_for_recovery":0,"trade_ready":False,
           "warning":"Name/symbol filtering is preliminary, no corporate-action adjustment or trade execution quote."}
    try:
        with gzip.open(BASE/"pilot_ohlcv.jsonl.gz","wt",encoding="utf-8") as output:
            for n,symbol in enumerate(selected):
                if n:time.sleep(1.5)
                stats["attempted"]+=1
                try:
                    rows=bars(symbol)
                    if len(rows)<150:
                        stats["insufficient_history"].append({"symbol":symbol,"valid_bars":len(rows)})
                        print(symbol,"insufficient history",len(rows),flush=True)
                        continue
                    output.write(json.dumps({"symbol":symbol,"bars":rows})+chr(10))
                    stats["stored"]+=1
                    print(symbol,"stored",len(rows),flush=True)
                except urllib.error.HTTPError as exc:
                    stats["failed"].append({"symbol":symbol,"http_status":exc.code})
                    if exc.code in (401,403,429):
                        stats["stopped_for_access_limit"]=True
                        break
                except Exception as exc:
                    stats["failed"].append({"symbol":symbol,"error":type(exc).__name__})
    finally:
        stats["finished_utc"]=datetime.now(timezone.utc).isoformat()
        (BASE/"pilot_stats.json").write_text(json.dumps(stats,indent=2),encoding="utf-8")
        print(json.dumps(stats,indent=2),flush=True)
    eligible=stats["attempted"]-len(stats["insufficient_history"])
    stats["eligible_with_150_bars"]=eligible
    stats["coverage_of_eligible"]=round(stats["stored"]/eligible,4) if eligible else 0
    stats["sample_completeness"]=round(stats["stored"]/stats["requested"],4) if stats["requested"] else 0
    (BASE/"pilot_stats.json").write_text(json.dumps(stats,indent=2),encoding="utf-8")
    if eligible<40 or stats["stored"]<0.9*eligible or stats.get("stopped_for_access_limit"):
        raise SystemExit("Pilot has too few eligible symbols, below 90% eligible coverage, or access-limited")
if __name__=="__main__":main()

