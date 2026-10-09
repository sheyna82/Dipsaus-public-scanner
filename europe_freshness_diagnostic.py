"""Diagnose stale Europe daily bars using independent Yahoo chart windows/hosts."""
import json,urllib.request,urllib.parse,urllib.error,time
from datetime import datetime,timezone,date
from pathlib import Path
from zoneinfo import ZoneInfo
SYMBOLS=["ASML.AS","SAP.DE","NOVO-B.CO","AZN.L","NESN.SW","MC.PA"]
OUT=Path("reports");OUT.mkdir(exist_ok=True)
def check(symbol,host,range_,interval):
    row={"symbol":symbol,"host":host,"range":range_,"interval":interval}
    url=f"https://{host}/v8/finance/chart/{urllib.parse.quote(symbol,safe='')}?range={range_}&interval={interval}&events=div%2Csplits"
    try:
        req=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0","Accept":"application/json","Cache-Control":"no-cache"})
        with urllib.request.urlopen(req,timeout=20) as resp:
            data=json.load(resp);row["http_status"]=resp.status
        result=(data.get("chart",{}).get("result") or [None])[0]
        if result is None:raise ValueError(str(data.get("chart",{}).get("error")))
        meta=result.get("meta") or {}
        tz=ZoneInfo(meta["exchangeTimezoneName"])
        times=result.get("timestamp") or []
        row.update(status="OK",currency=meta.get("currency"),exchange=meta.get("exchangeName"),
                   exchange_timezone=str(tz),market_state=meta.get("marketState"),
                   regular_market_time_utc=datetime.fromtimestamp(meta["regularMarketTime"],timezone.utc).isoformat() if meta.get("regularMarketTime") else None,
                   timestamp_count=len(times),last_three_local_dates=[datetime.fromtimestamp(t,timezone.utc).astimezone(tz).date().isoformat() for t in times[-3:]],
                   last_timestamp_utc=datetime.fromtimestamp(times[-1],timezone.utc).isoformat() if times else None)
    except Exception as e:row.update(status="ERROR",error=type(e).__name__)
    return row
def main():
    rows=[]
    for sym in SYMBOLS:
        for host,range_,interval in [("query1.finance.yahoo.com","2y","1d"),("query1.finance.yahoo.com","5d","1d"),("query2.finance.yahoo.com","5d","1d"),("query1.finance.yahoo.com","5d","1h")]:
            r=check(sym,host,range_,interval);rows.append(r)
            print(sym,host,range_,interval,r.get("last_three_local_dates"),r.get("error"),flush=True)
            time.sleep(.15)
    now=datetime.now(timezone.utc)
    report={"generated_utc":now.isoformat(),"scope":"Six exchange-diverse tickers; diagnostic only","results":rows,
            "interpretation":"Compare 2y vs 5d daily, query1 vs query2, and 1h bars. No prices promoted to trade signals."}
    (OUT/"europe_freshness_diagnostic.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
    ok=sum(r["status"]=="OK" for r in rows)
    print("successful_queries",ok,"of",len(rows))
    if ok<12:raise SystemExit("DATA-BLOCKED: too few successful diagnostic queries")
if __name__=="__main__":main()

