"""EODHD freshness supplement, separately sourced; never silently splice vendors."""
import gzip,json,os,urllib.parse,urllib.request,math
from datetime import datetime,timezone
from pathlib import Path
OUT=Path("reports")
# Explicit candidate mappings only. UK pence/GBP and unverified symbols excluded.
MAP={"ASML.AS":"ASML.AS","SAP.DE":"SAP.XETRA","MC.PA":"MC.PA",
     "NOVO-B.CO":"NOVO-B.CO","AZN.L":"AZN.LSE","NESN.SW":"NESN.SW"}
def valid(b):
    try:
        o,h,l,c,v=(float(b[k]) for k in ("open","high","low","close","volume"))
        return all(math.isfinite(x) for x in (o,h,l,c,v)) and l>0 and l<=min(o,c) and max(o,c)<=h and v>=0
    except (KeyError,TypeError,ValueError):return False
def main():
    audit=OUT/"europe_ohlcv_audit.json"
    if not audit.exists():raise SystemExit("DATA-BLOCKED: missing same-run Yahoo audit")
    data=json.loads(audit.read_text())
    token=os.environ.get("EODHD_API_TOKEN")
    rows=[]
    for source in data["results"]:
        symbol=source["symbol"]
        row={"symbol":symbol,"yahoo_last_complete_date":source.get("last_bar_date"),
             "status":"NOT_CHECKED","merge_performed":False}
        candidate=MAP.get(symbol)
        if not candidate:row.update(status="UNMAPPED",reason="No independently verified security mapping")
        elif not token:row.update(status="NOT_CONFIGURED",reason="EODHD_API_TOKEN absent")
        else:
            row["eodhd_symbol_candidate"]=candidate
            try:
                url="https://eodhd.com/api/eod/"+urllib.parse.quote(candidate,safe="")+"?"+urllib.parse.urlencode({
                    "api_token":token,"fmt":"json","from":"2026-09-14"})
                req=urllib.request.Request(url,headers={"User-Agent":"DipsausScanner/1.0","Accept":"application/json"})
                with urllib.request.urlopen(req,timeout=20) as response:bars=json.load(response)
                if not isinstance(bars,list):raise ValueError("Unexpected provider response")
                good=[b for b in bars if valid(b)]
                row.update(status="INDEPENDENT-COMPLETE-BARS" if good else "DATA-BLOCKED",
                           eodhd_last_complete_date=max((b["date"] for b in good),default=None),
                           complete_bar_count=len(good),invalid_bar_count=len(bars)-len(good),
                           latest_complete_bar=max(good,key=lambda b:b["date"]) if good else None,
                           identity_verified=False,currency_verified=False,unit_verified=False,
                           trade_ready=False)
            except Exception as e:row.update(status="DATA-BLOCKED",reason=type(e).__name__)
        rows.append(row)
        print(symbol,row["status"],row.get("eodhd_last_complete_date"),flush=True)
    report={"generated_utc":datetime.now(timezone.utc).isoformat(),
            "scope":"Same-run Yahoo audit plus independent EODHD control; 64-symbol pilot only",
            "source_audit":str(audit),"records":rows,"merged_into_ohlcv":False,
            "trade_ready":False,"note":"Ticker mappings are candidates, not independently verified ISIN/security IDs. Never mix unverified currencies, units or corporate-action adjustments."}
    (OUT/"europe_independent_supplement.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
if __name__=="__main__":main()

