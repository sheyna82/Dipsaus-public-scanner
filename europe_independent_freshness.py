"""Independent freshness cross-check. Never silently replace historical bars."""
import csv,io,json,os,urllib.parse,urllib.request
from datetime import datetime,timezone
from pathlib import Path
from zoneinfo import ZoneInfo
SYMBOLS=[("ASML.AS","asml.nl"),("SAP.DE","sap.de"),("MC.PA","mc.fr"),("NOVO-B.CO","novo-b.dk"),("AZN.L","azn.uk"),("NESN.SW","nesn.ch")]
OUT=Path("reports");OUT.mkdir(exist_ok=True)
def get(url):
    with urllib.request.urlopen(urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0","Accept":"application/json,text/csv"}),timeout=20) as r:
        return r.read().decode("utf-8")
def yahoo(sym):
    url="https://query1.finance.yahoo.com/v8/finance/chart/"+urllib.parse.quote(sym,safe="")+"?range=5d&interval=1d"
    obj=json.loads(get(url));r=(obj.get("chart",{}).get("result") or [None])[0]
    if not r:raise ValueError(str(obj.get("chart",{}).get("error")))
    m=r["meta"];tz=ZoneInfo(m["exchangeTimezoneName"]);t=r.get("timestamp") or []
    return {"source":"yahoo","symbol":sym,"currency":m.get("currency"),
            "last_bar_date":datetime.fromtimestamp(t[-1],timezone.utc).astimezone(tz).date().isoformat() if t else None,
            "regular_market_time":datetime.fromtimestamp(m["regularMarketTime"],timezone.utc).isoformat() if m.get("regularMarketTime") else None}
def stooq(sym,key):
    if not key:return {"source":"stooq","status":"NOT_CONFIGURED","reason":"STOOQ_APIKEY secret absent"}
    url="https://stooq.com/q/d/l/?"+urllib.parse.urlencode({"s":sym,"i":"d","d1":"20260914","apikey":key})
    body=get(url)
    rows=list(csv.DictReader(io.StringIO(body)))
    if not rows or not {"Date","Close"}.issubset(rows[0]):
        return {"source":"stooq","status":"DATA-BLOCKED","reason":"No valid CSV; key/coverage/symbol may be invalid"}
    valid=[r for r in rows if r.get("Date") and r.get("Close") not in ("",None,"N/D")]
    return {"source":"stooq","status":"PASS" if valid else "DATA-BLOCKED",
            "last_bar_date":max(r["Date"] for r in valid) if valid else None,
            "note":"Symbol mapping is unverified; do not merge prices until identity, exchange, currency and units are confirmed"}
def main():
    key=os.environ.get("STOOQ_APIKEY","")
    rows=[]
    for sym,alternative in SYMBOLS:
        entry={"yahoo_symbol":sym,"stooq_symbol_candidate":alternative}
        for name,fn in (("yahoo",lambda:yahoo(sym)),("stooq",lambda:stooq(alternative,key))):
            try:entry[name]=fn()
            except Exception as exc:entry[name]={"status":"DATA-BLOCKED","reason":type(exc).__name__}
        rows.append(entry)
        print(sym,"yahoo",entry["yahoo"].get("last_bar_date"),"stooq",entry["stooq"].get("last_bar_date"),flush=True)
    report={"generated_utc":datetime.now(timezone.utc).isoformat(),"scope":"Six-symbol independent source diagnostic, not market-wide",
            "stooq_key_configured":bool(key),"rows":rows,
            "warning":"No alternate prices are merged into OHLCV; candidate Stooq symbols not identity-verified. No live quote or trade signal."}
    (OUT/"europe_independent_freshness.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
    print("report_written",len(rows))
if __name__=="__main__":main()

