"""Freshness and bid/ask audit. Provider data is discovery evidence, never a DEGIRO quote/order."""
import json,math,time,urllib.parse,urllib.request
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path("reports")
LIVE_MAX_AGE_SECONDS=120
DELAYED_MAX_AGE_SECONDS=20*60
MAX_SPREAD_PCT=0.35

def finite_positive(x):
    return isinstance(x,(int,float)) and not isinstance(x,bool) and math.isfinite(x) and x>0

def audit(meta,stamps,closes,now):
    last=max(((t,c) for t,c in zip(stamps,closes) if isinstance(t,(int,float)) and finite_positive(c)),default=None)
    bid=meta.get("bid");ask=meta.get("ask")
    spread=(ask-bid)/((ask+bid)/2)*100 if finite_positive(bid) and finite_positive(ask) and ask>=bid else None
    age=now-last[0] if last else None
    currency=meta.get("currency")
    live=age is not None and 0<=age<=LIVE_MAX_AGE_SECONDS
    delayed=age is not None and LIVE_MAX_AGE_SECONDS<age<=DELAYED_MAX_AGE_SECONDS
    if live:freshness="LIVE-LIKE-PROVIDER"
    elif delayed:freshness="DELAYED-PROVIDER"
    elif age is None:freshness="NO-VALID-QUOTE"
    else:freshness="STALE-OR-TIMESTAMP-INVALID"
    reasons=[]
    if last is None:reasons.append("NO-VALID-1M-QUOTE")
    if freshness=="DELAYED-PROVIDER":reasons.append("PROVIDER-DELAYED-VERIFY-BROKER-NOW")
    elif not live:reasons.append("QUOTE-STALE-OR-TIMESTAMP-INVALID")
    if spread is None:reasons.append("NO-VALID-BID-ASK")
    elif spread>MAX_SPREAD_PCT:reasons.append("SPREAD-TOO-WIDE")
    reasons.append("BROKER-QUOTE-NOT-VERIFIED")
    return {"provider":"Yahoo Finance 1m chart","currency":currency,
            "quote_utc":datetime.fromtimestamp(last[0],timezone.utc).isoformat() if last else None,
            "quote_close":last[1] if last else None,"quote_age_seconds":round(age,1) if age is not None else None,
            "provider_bid":bid if finite_positive(bid) else None,"provider_ask":ask if finite_positive(ask) else None,
            "provider_spread_pct":round(spread,4) if spread is not None else None,
            "provider_freshness_class":freshness,"provider_freshness_pass":live,
            "provider_delayed_but_usable_for_attention":delayed,
            "broker_quote_verified":False,"exchange_open_verified":False,
            "executable_price_verified":False,"trade_ready":False,"execution_blocks":reasons}

def fetch(symbol):
    # Retry transient/rate-limit failures; missing provider data must be reported as
    # DATA-BLOCKED, never misrepresented as NO-SETUP.
    url="https://query1.finance.yahoo.com/v8/finance/chart/"+urllib.parse.quote(symbol,safe="")+"?range=1d&interval=1m"
    data=None
    last_exc=None
    for attempt in range(3):
        try:
            req=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0","Accept":"application/json","Cache-Control":"no-cache"})
            with urllib.request.urlopen(req,timeout=20) as f:data=json.load(f)
            break
        except Exception as exc:
            last_exc=exc
            if attempt<2: time.sleep(1+attempt)
    if data is None: raise last_exc or ValueError("Provider request failed")
    result=(data.get("chart",{}).get("result") or [None])[0]
    if not result:raise ValueError("No chart result")
    meta=result.get("meta") or {}
    if meta.get("symbol")!=symbol:raise ValueError("Symbol mismatch")
    return meta,result.get("timestamp") or [],(result["indicators"]["quote"][0].get("close") or [])

def main():
    source=json.loads((ROOT/"europe_intraday_confirmation.json").read_text());now=datetime.now(timezone.utc);out=[]
    for candidate in source["candidates"]:
        sym=candidate["symbol"];row={"symbol":sym,"intraday_status":candidate.get("data_status"),"trade_ready":False}
        try:
            meta,stamps,closes=fetch(sym);row.update(audit(meta,stamps,closes,now.timestamp()))
            if row["currency"]!=candidate.get("currency"):row["execution_blocks"].append("CURRENCY-MISMATCH")
        except Exception as exc:
            row.update(execution_blocks=["QUOTE-DATA-BLOCKED","BROKER-QUOTE-NOT-VERIFIED"],reason=type(exc).__name__,broker_quote_verified=False,executable_price_verified=False,provider_freshness_class="DATA-BLOCKED",provider_delayed_but_usable_for_attention=False)
        out.append(row);print(json.dumps(row,ensure_ascii=False),flush=True)
    result={"generated_utc":now.isoformat(),"scope":"Provider quote audit. <=2m is live-like provider evidence; 2-20m is delayed attention evidence only; DEGIRO still required for execution.","checked":len(out),"trade_ready_count":0,"candidates":out}
    (ROOT/"europe_quote_execution_audit.json").write_text(json.dumps(result,indent=2,ensure_ascii=False))
    print(json.dumps({k:v for k,v in result.items() if k!="candidates"},indent=2))
if __name__=="__main__":main()

