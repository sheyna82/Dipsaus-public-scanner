"""Descriptive post-event OHLCV outcomes; never treat unverified dates as trade signals."""
import argparse, collections, json
from datetime import date
from pathlib import Path

HORIZONS=(3,5,10,15)

def summarize(events, prices_by_symbol):
    rows=[]; rejected=collections.Counter(); seen=set()
    for event in events:
        symbol=event.get("ticker"); day=event.get("date")
        try: date.fromisoformat(day)
        except (TypeError,ValueError): rejected["bad_event_date"]+=1;continue
        key=(symbol,day)
        if key in seen: rejected["duplicate_symbol_day"]+=1;continue
        seen.add(key)
        bars=prices_by_symbol.get(symbol)
        if not bars:rejected["missing_prices"]+=1;continue
        # Strictly AFTER the reported date, to avoid assuming an intraday publication time.
        entry_index=next((i for i,b in enumerate(bars) if b["date"]>day),None)
        if entry_index is None:rejected["no_later_session"]+=1;continue
        entry=bars[entry_index]["open"]
        if not isinstance(entry,(float,int)) or entry<=0:rejected["bad_entry"]+=1;continue
        for horizon in HORIZONS:
            exit_index=entry_index+horizon-1
            if exit_index>=len(bars):
                rejected["insufficient_forward_sessions"]+=1
                continue
            end=bars[exit_index]["close"]
            if not isinstance(end,(float,int)) or end<=0:rejected["bad_exit"]+=1;continue
            rows.append({"symbol":symbol,"event_date":day,"entry_date":bars[entry_index]["date"],"exit_date":bars[exit_index]["date"],"horizon":horizon,"gross_return_pct":round(100*(end/entry-1),6)})
    cohorts=[]
    for horizon in HORIZONS:
        sample=[r["gross_return_pct"] for r in rows if r["horizon"]==horizon]
        cohorts.append({"horizon":horizon,"n":len(sample),"mean_gross_pct":round(sum(sample)/len(sample),5) if sample else None,"positive_fraction":round(sum(x>0 for x in sample)/len(sample),5) if sample else None})
    return {"outcome_rows":len(rows),"cohorts":cohorts,"rejections":dict(rejected),"timestamp_verified":False,"point_in_time_verified":False,"trade_ready":False,"predictive_edge_proven":False,"method":"next-session-open to horizon-th-session-close; descriptive only; gross before costs","rows":rows}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--events-dir",required=True)
    p.add_argument("--prices-dir",required=True)
    p.add_argument("--output",required=True)
    args=p.parse_args()
    prices={}
    for f in sorted(Path(args.prices_dir).glob("prices_*.json")):
        data=json.loads(f.read_text());prices[data["symbol"]]=data["bars"]
    events=[]
    for f in sorted(Path(args.events_dir).glob("source_*.json")):
        data=json.loads(f.read_text())
        payload=data.get("data",data) if isinstance(data,dict) else data
        records=payload.get("releases",[]) if isinstance(payload,dict) else payload
        if not isinstance(records,list):raise ValueError("bad_event_source")
        events.extend(x for x in records if isinstance(x,dict) and x.get("status")=="reported")
    result=summarize(events,prices)
    Path(args.output).write_text(json.dumps(result,indent=2))
    print(json.dumps({k:v for k,v in result.items() if k!="rows"}))
if __name__=="__main__":main()
