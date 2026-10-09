"""Bounded, auditable European OHLCV pilot. Not a full-Europe scan or trade signals."""
import gzip, json, math, time, urllib.parse, urllib.request
from datetime import datetime, timezone, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

# Diverse exchanges and sectors; this is a fixed pilot, not market-wide discovery.
UNIVERSE = {
 "healthcare":["NOVO-B.CO","NOVN.SW","ROG.SW","SAN.PA","GSK.L","AZN.L","BAYN.DE","IPN.PA"],
 "industrials":["SIE.DE","SU.PA","ABB.SW","SAF.PA","AIR.PA","VOW3.DE","RHM.DE","HEI.DE"],
 "financials":["BNP.PA","GLE.PA","INGA.AS","DBK.DE","UBSG.SW","HSBA.L","ISP.MI","SAN.MC"],
 "materials_chemicals":["BAS.DE","BNR.DE","EVK.DE","LXS.DE","AKE.PA","CRH.L","GLEN.L","RIO.L"],
 "consumer":["MC.PA","OR.PA","KER.PA","ADS.DE","ZAL.DE","NESN.SW","ULVR.L","ITX.MC"],
 "energy_utilities":["SHEL.L","BP.L","TTE.PA","ENI.MI","RWE.DE","EOAN.DE","IBE.MC","ENGI.PA"],
 "technology_telecom":["ASML.AS","ASM.AS","BESI.AS","SAP.DE","IFX.DE","AIXA.DE","SOI.PA","NOKIA.HE"],
 "transport_logistics":["DHL.DE","DSV.CO","MAERSK-B.CO","AF.PA","IAG.L","LHA.DE","HLAG.DE","WIZZ.L"],
}
# Expansion candidates are additional research coverage, not pre-approved trades.
EXPANSION = {
 "healthcare":["UCB.BR","PHIA.AS","FRE.DE","SRT3.DE"],
 "industrials":["MTX.DE","PRY.MI","ALFEN.AS","VIE.PA"],
 "financials":["ABN.AS","KBC.BR","ACA.PA","CBK.DE"],
 "materials_chemicals":["UMI.BR","SOLB.BR","NDA-FI.HE","STERV.HE"],
 "consumer":["PUM.DE","BIRG.IR","RNO.PA","MBG.DE"],
 "energy_utilities":["EDPR.LS","ORSTED.CO","VWS.CO","NEL.OL"],
 "technology_telecom":["ADYEN.AS","STM.PA","LOGN.SW","ERIC-B.ST"],
 "transport_logistics":["KNIN.SW","POST.VI","BOL.ST","GETI-B.ST"],
 "broad_liquid":["AKZA.AS","RAND.AS","UNA.AS","IMCD.AS","WKL.AS","LIGHT.AS","BEI.DE","HEN3.DE","FME.DE","CON.DE","DTG.DE","NEM.DE","CAP.PA","HO.PA","ALO.PA","DG.PA","SGO.PA","RI.PA","VIV.PA","PUB.PA","MONC.MI","STLAM.MI","TEN.MI","DIA.MI","AMP.MI","FER.MC","ACS.MC","REP.MC","TEF.MC","CABK.MC","BBVA.MC","CARL-B.CO","PNDORA.CO","DEMANT.CO","GN.CO","ISS.CO","ATCO-A.ST","SAND.ST","SKF-B.ST","SWED-A.ST","SEB-A.ST","TELIA.ST","EQT.ST","NIBE-B.ST","KNEBV.HE","UPM.HE","FORTUM.HE","METSO.HE","ELISA.HE","DNB.OL","EQNR.OL","NHY.OL","TEL.OL","ORK.OL","YAR.OL"]
}
for sector, symbols in EXPANSION.items():
    UNIVERSE.setdefault(sector, []).extend(symbols)
OUT=Path("reports");OUT.mkdir(exist_ok=True)
def fetch(symbol,sector):
    row={"symbol":symbol,"sector":sector,"status":"DATA-BLOCKED"}
    url="https://query1.finance.yahoo.com/v8/finance/chart/"+urllib.parse.quote(symbol,safe="")+"?range=2y&interval=1d"
    for attempt in range(3):
        try:
            request=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0","Accept":"application/json"})
            with urllib.request.urlopen(request,timeout=20) as response: data=json.load(response)
            result=(data.get("chart",{}).get("result") or [None])[0]
            if not result: raise ValueError(str(data.get("chart",{}).get("error")))
            meta=result.get("meta") or {}
            tz=ZoneInfo(meta["exchangeTimezoneName"])
            quotes=result["indicators"]["quote"][0]
            bars=[]
            for i,stamp in enumerate(result.get("timestamp") or []):
                try:
                    o,h,l,c,v=[quotes[k][i] for k in ("open","high","low","close","volume")]
                    if not all(isinstance(x,(int,float)) and math.isfinite(x) for x in (o,h,l,c,v)):continue
                    if l<=0 or l>min(o,c) or max(o,c)>h or v<0:continue
                    day=datetime.fromtimestamp(stamp,timezone.utc).astimezone(tz).date().isoformat()
                    bars.append([day,round(o,5),round(h,5),round(l,5),round(c,5),int(v)])
                except (KeyError,IndexError,TypeError,ValueError):continue
            bars=list({b[0]:b for b in bars}.values());bars.sort()
            currency=meta.get("currency")
            row.update(currency=currency,exchange=meta.get("exchangeName"),timezone=meta.get("exchangeTimezoneName"),
                       returned_symbol=meta.get("symbol"),valid_bars=len(bars),
                       first_bar_date=bars[0][0] if bars else None,last_bar_date=bars[-1][0] if bars else None)
            if meta.get("symbol")!=symbol or len(bars)<150 or not currency:
                row["reason"]="Symbol, history or currency validation failed"
                return row,None
            # A short-window request can expose newer daily bars than the long-window response.
            # Never merge unless symbol, currency, exchange and timezone match exactly.
            recent_url="https://query1.finance.yahoo.com/v8/finance/chart/"+urllib.parse.quote(symbol,safe="")+"?range=5d&interval=1d"
            try:
                recent_req=urllib.request.Request(recent_url,headers={"User-Agent":"Mozilla/5.0","Accept":"application/json","Cache-Control":"no-cache"})
                with urllib.request.urlopen(recent_req,timeout=20) as response: recent_data=json.load(response)
                recent=(recent_data.get("chart",{}).get("result") or [None])[0]
                if not recent:raise ValueError("Missing recent result")
                rm=recent.get("meta") or {}
                if any(rm.get(k)!=meta.get(k) for k in ("symbol","currency","exchangeName","exchangeTimezoneName")):
                    raise ValueError("Recent source identity/currency/exchange/timezone mismatch")
                rq=recent["indicators"]["quote"][0]
                extra=[]
                for i,stamp in enumerate(recent.get("timestamp") or []):
                    try:
                        o,h,l,c,v=[rq[k][i] for k in ("open","high","low","close","volume")]
                        if not all(isinstance(x,(int,float)) and math.isfinite(x) for x in (o,h,l,c,v)):continue
                        if l<=0 or l>min(o,c) or max(o,c)>h or v<0:continue
                        day=datetime.fromtimestamp(stamp,timezone.utc).astimezone(tz).date().isoformat()
                        extra.append([day,round(o,5),round(h,5),round(l,5),round(c,5),int(v)])
                    except (KeyError,IndexError,TypeError,ValueError):continue
                if not extra:raise ValueError("No valid recent OHLCV")
                old_last=bars[-1][0]
                bars=sorted({b[0]:b for b in bars+extra}.values())
                row.update(long_window_last_date=old_last,recent_window_last_date=max(b[0] for b in extra),
                           last_bar_date=bars[-1][0],valid_bars=len(bars),recent_merge_status="PASS")
            except Exception as exc:
                row["recent_merge_status"]="DATA-BLOCKED"
                row["recent_merge_reason"]=type(exc).__name__
            row["status"]="PASS"
            return row,{"symbol":symbol,"sector":sector,"currency":currency,"exchange":meta.get("exchangeName"),"bars":bars}
        except Exception as exc:
            row["reason"]=type(exc).__name__
            if attempt<2:time.sleep(attempt+1)
    return row,None


def freshness_audit(results):
    """Previous weekday is an explicit provisional benchmark, not a holiday calendar."""
    from datetime import date
    today=datetime.now(timezone.utc).date()
    expected=today-timedelta(days=1)
    while expected.weekday()>=5:expected-=timedelta(days=1)
    stale=[r["symbol"] for r in results if r["status"]=="PASS" and
           date.fromisoformat(r["last_bar_date"])<expected]
    unverified=[r["symbol"] for r in results if r["status"]=="PASS" and
                r.get("recent_merge_status")!="PASS"]
    return {"checked_utc":datetime.now(timezone.utc).isoformat(),
            "expected_previous_weekday":expected.isoformat(),
            "stale_symbols":stale,"recent_merge_unverified":unverified,
            "freshness_passed":not stale and not unverified,
            "note":"Previous weekday benchmark only; exchange holidays and intraday completeness NOT verified. Not a live quote."}

def main():
    results=[];records=[]
    for sector,symbols in UNIVERSE.items():
        for symbol in symbols:
            row,record=fetch(symbol,sector)
            results.append(row)
            if record:records.append(record)
            print(symbol,row["status"],row.get("last_bar_date"),flush=True)
            time.sleep(.25)
    with gzip.open(OUT/"europe_ohlcv.jsonl.gz","wt",encoding="utf-8") as f:
        for record in records:f.write(json.dumps(record,separators=(",",":"))+"\n")
    dates={}
    for row in results:
        date=row.get("last_bar_date")
        if date:dates[date]=dates.get(date,0)+1
    report={"generated_utc":datetime.now(timezone.utc).isoformat(),"scope":"Expanded liquid European recovery universe across major exchanges; still NOT a complete European market scan",
            "attempted":len(results),"passed":len(records),"blocked":len(results)-len(records),
            "last_bar_dates":dates,"live_quotes_verified":False,"trade_ready":False,
            "warning":"Unadjusted Yahoo daily bars; latest day may be incomplete or delayed; no corporate-action adjustment, FX, fundamentals, news, resistance or swing calculation.",
            "results":results}
    report["freshness"]=freshness_audit(results)
    (OUT/"europe_ohlcv_audit.json").write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding="utf-8")
    print(json.dumps({k:v for k,v in report.items() if k!="results"},indent=2))
    # Coverage is graded rather than all-or-nothing: isolated provider failures should not
    # discard a healthy same-run market refresh. The failed names remain excluded.
    coverage_ratio=len(records)/len(results) if results else 0
    report["coverage_ratio"]=round(coverage_ratio,4)
    report["research_refresh_usable"]=coverage_ratio>=0.90 and report["freshness"]["freshness_passed"]
    (OUT/"europe_ohlcv_audit.json").write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding="utf-8")
    if coverage_ratio<0.90:
        raise SystemExit("DATA-BLOCKED: fewer than 90% of symbols produced valid same-run OHLCV")
    if not report["freshness"]["freshness_passed"]:
        raise SystemExit("STALE-DATA: OHLCV artifact retained for historical research; current trade signals blocked")
if __name__=="__main__":main()

