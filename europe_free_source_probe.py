"""Independent no-key European quote-source probe; research only."""
import csv,io,json,urllib.request,urllib.parse
from datetime import datetime,timezone
from pathlib import Path
OUT=Path("reports");OUT.mkdir(exist_ok=True)
# Unverified mappings: NEVER merge or infer identity/currency from symbol alone.
TESTS=[("EDPR.LS","edpr.pt"),("ASML.AS","asml.nl"),("SAP.DE","sap.de"),
       ("SAN.PA","san.fr"),("PRY.MI","pry.it"),("AZN.L","azn.uk")]
def probe(symbol, candidate):
    row={"yahoo_symbol":symbol,"stooq_candidate":candidate,"identity_verified":False,
         "currency_verified":False,"provider_freshness_pass":False,"trade_ready":False}
    try:
        url="https://stooq.com/q/d/l/?"+urllib.parse.urlencode({"s":candidate,"i":"d"})
        req=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0","Accept":"text/csv"})
        with urllib.request.urlopen(req,timeout=15) as f:
            body=f.read(250000).decode("utf-8-sig",errors="replace")
        if body.lstrip().startswith("<"):
            row.update(status="HTML_OR_CHALLENGE_INSTEAD_OF_CSV")
        else:
            bars=list(csv.DictReader(io.StringIO(body)))
            good=[b for b in bars if b.get("Date") and b.get("Close") and b.get("Volume")]
            row.update(status="HISTORICAL_CSV_AVAILABLE" if good else "NO_VALID_CSV",
                       valid_rows=len(good),last_date=good[-1]["Date"] if good else None,
                       latest_close=good[-1]["Close"] if good else None)
    except Exception as exc:
        row.update(status="ERROR",error=type(exc).__name__)
    return row
def main():
    rows=[probe(*t) for t in TESTS]
    report={"generated_utc":datetime.now(timezone.utc).isoformat(),
       "status":"INDEPENDENT_SOURCE_PROBE_ONLY","source":"Stooq public daily CSV",
       "no_key_required":True,"symbols_requested":len(TESTS),
       "symbols_with_historical_csv":sum(x["status"]=="HISTORICAL_CSV_AVAILABLE" for x in rows),
       "symbols_with_verified_live_quotes":0,"trade_ready":False,
       "warning":"Daily CSV is NOT intraday/realtime. Mappings, currency and corporate actions unverified; never merge into executable quotes.",
       "results":rows}
    (OUT/"europe_free_source_probe.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
    print(json.dumps(report,indent=2))
if __name__=="__main__":main()

