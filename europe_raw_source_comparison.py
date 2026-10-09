"""Preserve exact Yahoo 2y/5d responses and compare source timestamps; no trade signals."""
import gzip,json,urllib.parse,urllib.request
from datetime import datetime,timezone
from pathlib import Path
from zoneinfo import ZoneInfo
SYMBOLS=["ASML.AS","SAP.DE","NOVO-B.CO","AZN.L","NESN.SW","MC.PA"]
OUT=Path("reports");OUT.mkdir(exist_ok=True)
def main():
    traces=[]
    with gzip.open(OUT/"europe_raw_source_comparison.jsonl.gz","wt",encoding="utf-8") as raw:
        for symbol in SYMBOLS:
            for period in ("2y","5d"):
                row={"symbol":symbol,"period":period,"requested_utc":datetime.now(timezone.utc).isoformat()}
                url="https://query1.finance.yahoo.com/v8/finance/chart/"+urllib.parse.quote(symbol,safe="")+"?range="+period+"&interval=1d"
                try:
                    req=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0","Accept":"application/json","Cache-Control":"no-cache"})
                    with urllib.request.urlopen(req,timeout=20) as response:
                        data=json.load(response);row["http_status"]=response.status
                    raw.write(json.dumps({"symbol":symbol,"period":period,"response":data},separators=(",",":"))+"\n")
                    result=(data.get("chart",{}).get("result") or [None])[0]
                    if not result:raise ValueError(str(data.get("chart",{}).get("error")))
                    meta=result.get("meta") or {}
                    tz=ZoneInfo(meta["exchangeTimezoneName"])
                    stamps=result.get("timestamp") or []
                    quotes=result["indicators"]["quote"][0]
                    row.update(status="OK",returned_symbol=meta.get("symbol"),currency=meta.get("currency"),
                               exchange=meta.get("exchangeName"),timezone=str(tz),count=len(stamps),
                               last_timestamps_utc=[datetime.fromtimestamp(t,timezone.utc).isoformat() for t in stamps[-5:]],
                               last_local_dates=[datetime.fromtimestamp(t,timezone.utc).astimezone(tz).date().isoformat() for t in stamps[-5:]],
                               last_quotes={k:v[-5:] for k,v in quotes.items() if isinstance(v,list)},
                               regular_market_time_utc=datetime.fromtimestamp(meta["regularMarketTime"],timezone.utc).isoformat() if meta.get("regularMarketTime") else None)
                except Exception as e:row.update(status="ERROR",reason=type(e).__name__)
                traces.append(row)
                print(symbol,period,row.get("last_local_dates"),row.get("reason"),flush=True)
    (OUT/"europe_source_comparison.json").write_text(json.dumps({"generated_utc":datetime.now(timezone.utc).isoformat(),
        "note":"Exact source responses for six test names; raw data are untrusted, not adjusted or live.",
        "results":traces},indent=2),encoding="utf-8")
if __name__=="__main__":main()

