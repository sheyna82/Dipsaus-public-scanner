"""Link unverified earnings records to historical Yahoo OHLCV, research only."""
import argparse, collections, datetime as dt, hashlib, json, time, urllib.request
from pathlib import Path
from zoneinfo import ZoneInfo

def load_events(root):
    rows=[]
    for path in sorted(Path(root).glob("source_*.json")):
        payload=json.loads(path.read_text())
        data=payload.get("data",payload) if isinstance(payload,dict) else payload
        if isinstance(data,dict): data=data.get("releases",[])
        if not isinstance(data,list): raise ValueError("unexpected_source_shape")
        rows.extend(x for x in data if isinstance(x,dict) and x.get("ticker") and x.get("date") and x.get("accessionNo") and x.get("status")=="reported")
    if not rows: raise ValueError("no_events")
    return rows

def fetch_bars(symbol):
    start=int(dt.datetime(2026,2,1,tzinfo=dt.timezone.utc).timestamp())
    end=int(dt.datetime(2026,10,28,tzinfo=dt.timezone.utc).timestamp())
    from urllib.parse import quote
    url=f"https://query1.finance.yahoo.com/v8/finance/chart/{quote(symbol,safe='')}?period1={start}&period2={end}&interval=1d"
    req=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0"})
    with urllib.request.urlopen(req,timeout=25) as response: body=response.read(3000000)
    obj=json.loads(body)["chart"]
    if obj.get("error"): raise ValueError("chart_error")
    item=obj["result"][0]
    if item["meta"]["symbol"].upper()!=symbol.upper(): raise ValueError("symbol_mismatch")
    quote_data=item["indicators"]["quote"][0]
    bars=[]
    for i,stamp in enumerate(item.get("timestamp",[])):
        vals=[quote_data[k][i] for k in ("open","high","low","close","volume")]
        if any(x is None for x in vals):continue
        o,h,l,c,v=vals
        if not (0<l<=min(o,c)<=max(o,c)<=h and v>=0):raise ValueError("invalid_ohlcv")
        day=dt.datetime.fromtimestamp(stamp,dt.timezone.utc).astimezone(ZoneInfo("America/New_York")).date().isoformat()
        bars.append({"date":day,"open":o,"high":h,"low":l,"close":c,"volume":v})
    if not bars or any(a["date"]>=b["date"] for a,b in zip(bars,bars[1:])):raise ValueError("invalid_sessions")
    return bars,hashlib.sha256(body).hexdigest()

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--events-dir",required=True)
    p.add_argument("--output-dir",required=True)
    p.add_argument("--max-symbols",type=int,default=200)
    p.add_argument("--shard-index",type=int,default=0)
    p.add_argument("--shard-count",type=int,default=1)
    args=p.parse_args()
    if not 1<=args.max_symbols<=200:raise ValueError("invalid_batch_size")
    if not 1<=args.shard_count<=40 or not 0<=args.shard_index<args.shard_count:raise ValueError("invalid_shard")
    out=Path(args.output_dir);out.mkdir(parents=True,exist_ok=True)
    events=load_events(args.events_dir)
    counts=collections.Counter(x["ticker"] for x in events)
    ordered=sorted(counts,key=lambda s:(-counts[s],s))
    selected=ordered[args.shard_index*args.max_symbols:(args.shard_index+1)*args.max_symbols]
    report=[]
    for symbol in selected:
        row={"symbol":symbol,"event_count":counts[symbol],"timestamp_verified":False}
        try:
            bars,digest=fetch_bars(symbol)
            (out/("prices_"+symbol.replace("/","_")+".json")).write_text(json.dumps({"symbol":symbol,"bars":bars,"source":"Yahoo Chart unverified"}))
            row.update(status="downloaded_unverified",bars=len(bars),raw_sha256=digest)
        except Exception as exc:
            row.update(status="failed",reason=type(exc).__name__+":"+str(exc)[:100])
        report.append(row)
        time.sleep(2)
    summary={"total_events":len(events),"unique_symbols":len(counts),"selected_symbols":len(selected),"successful_symbols":sum(x["status"]=="downloaded_unverified" for x in report),"linked_events":sum(counts[x["symbol"]] for x in report if x["status"]=="downloaded_unverified"),"timestamp_verified":False,"trade_ready":False,"results":report}
    (out/"linkage_report.json").write_text(json.dumps(summary,indent=2))
    print(json.dumps({k:v for k,v in summary.items() if k!="results"}))
if __name__=="__main__":main()
