"""Independent complete OHLCV check: EODHD vs Yahoo, no invented or mixed prices."""
import json,os,urllib.parse,urllib.request,urllib.error
from datetime import datetime,timezone
from pathlib import Path
SYMBOLS=[("ASML.AS","ASML.AS"),("SAP.DE","SAP.XETRA"),("MC.PA","MC.PA"),
         ("NOVO-B.CO","NOVO-B.CO"),("AZN.L","AZN.LSE"),("NESN.SW","NESN.SW")]
OUT=Path("reports");OUT.mkdir(exist_ok=True)
def request_json(url):
    with urllib.request.urlopen(urllib.request.Request(url,headers={"User-Agent":"DipsausScanner/1.0","Accept":"application/json"}),timeout=20) as response:
        return json.load(response)
def valid(o,h,l,c,v):
    import math
    vals=(o,h,l,c,v)
    return all(isinstance(x,(int,float)) and math.isfinite(x) for x in vals) and l>0 and l<=min(o,c) and max(o,c)<=h and v>=0
def check(symbol,provider_symbol,key):
    row={"yahoo_symbol":symbol,"eodhd_symbol_candidate":provider_symbol,
         "provider":"EODHD","trade_ready":False}
    if not key:return dict(row,status="NOT_CONFIGURED",reason="EODHD_API_TOKEN GitHub secret not set")
    url="https://eodhd.com/api/eod/"+urllib.parse.quote(provider_symbol,safe="")+"?"+urllib.parse.urlencode({
        "api_token":key,"fmt":"json","from":"2026-09-14"})
    try:
        data=request_json(url)
        if not isinstance(data,list):raise ValueError("Non-array provider response: "+str(data)[:130])
        good=[];invalid=0
        for b in data:
            try:
                o,h,l,c,v=[float(b[k]) for k in ("open","high","low","close","volume")]
                if not valid(o,h,l,c,v):raise ValueError("invalid OHLCV")
                good.append({"date":b["date"],"open":o,"high":h,"low":l,"close":c,"volume":v})
            except (KeyError,TypeError,ValueError):invalid+=1
        row.update(status="RESEARCH-ONLY" if good else "DATA-BLOCKED",
                   last_complete_date=max((b["date"] for b in good),default=None),
                   complete_bars=len(good),invalid_bars=invalid,last_two_bars=good[-2:],
                   identity_verified=False,currency_verified=False,unit_verified=False,
                   note="Candidate ticker mapping only; verify exchange, security ID, currency, GBp/GBP, splits before merging")
    except Exception as e:row.update(status="DATA-BLOCKED",reason=type(e).__name__)
    return row
def main():
    key=os.environ.get("EODHD_API_TOKEN","")
    rows=[check(sym,candidate,key) for sym,candidate in SYMBOLS]
    report={"generated_utc":datetime.now(timezone.utc).isoformat(),
            "scope":"Six-symbol independent provider check, not a complete European refresh",
            "key_configured":bool(key),"rows":rows,"live_quotes_verified":False,
            "no_automatic_merge":True,"trade_ready":False}
    (OUT/"europe_eodhd_source_check.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
    for r in rows:print(r["yahoo_symbol"],r["status"],r.get("last_complete_date"),r.get("reason"),flush=True)
if __name__=="__main__":main()

