#!/usr/bin/env python3
"""Broad, fast US recovery discovery.

Discovery is intentionally broader than execution. It searches liquid large/mid-cap
US stocks from both most-active and day-gainer universes, then recognises an
intraday bottom -> higher-low -> reclaim pattern. Research/pre-alert only; never a
buy signal.
"""
import csv, io, json, math, re, urllib.parse, urllib.request
from datetime import datetime, timezone
from pathlib import Path

OUT=Path("reports/us_momentum_recovery.json")
HEADERS={"User-Agent":"Mozilla/5.0 (compatible; DipsausMomentum/2.0)"}
SCREENER="https://query1.finance.yahoo.com/v1/finance/screener/predefined/saved"
CHART="https://query1.finance.yahoo.com/v8/finance/chart/"
# Current-security identity boundary for reused tickers.
LISTING_START_UTC={"SPCX":datetime(2026,6,12,tzinfo=timezone.utc).timestamp()}

def get_json(url, params=None):
    if params: url += "?" + urllib.parse.urlencode(params)
    req=urllib.request.Request(url,headers=HEADERS)
    with urllib.request.urlopen(req,timeout=15) as r: return json.loads(r.read().decode())

def chart(symbol, rng, interval):
    d=get_json(CHART+urllib.parse.quote(symbol),{"range":rng,"interval":interval,"includePrePost":"false"})
    res=d["chart"]["result"][0]; q=res["indicators"]["quote"][0]; ts=res.get("timestamp",[])
    rows=[]
    for i,(h,l,c,v) in enumerate(zip(q["high"],q["low"],q["close"],q["volume"])):
        if None in (h,l,c,v): continue
        vals=[float(h),float(l),float(c),float(v)]
        if all(math.isfinite(x) for x in vals) and min(vals[:3])>0:
            rows.append({"ts":ts[i] if i<len(ts) else None,"high":vals[0],"low":vals[1],"close":vals[2],"volume":vals[3]})
    start=LISTING_START_UTC.get(symbol)
    if start is not None: rows=[r for r in rows if r.get("ts") is not None and r["ts"]>=start]
    return rows

def universe():
    """Broad official US equity universe; Yahoo screeners only enrich current quote metadata."""
    found={}
    urls=(
      "https://www.nasdaqtrader.com/dynamic/SymDir/nasdaqlisted.txt",
      "https://www.nasdaqtrader.com/dynamic/SymDir/otherlisted.txt",
    )
    for url in urls:
        req=urllib.request.Request(url,headers=HEADERS)
        with urllib.request.urlopen(req,timeout=20) as r:
            raw=r.read().decode("utf-8-sig")
        rows=csv.DictReader((line for line in raw.splitlines() if not line.startswith("File Creation Time")),delimiter="|")
        for row in rows:
            symbol=(row.get("Symbol") or row.get("NASDAQ Symbol") or row.get("ACT Symbol") or "").strip()
            name=(row.get("Security Name") or "").strip()
            if row.get("Test Issue")!="N" or row.get("ETF")!="N": continue
            if not re.fullmatch(r"[A-Z]{1,5}",symbol): continue
            low=name.lower()
            if any(x in low for x in ("warrant"," right"," unit","preferred","preference"," etf"," fund"," note"," bond")): continue
            found[symbol]={"symbol":symbol,"shortName":name}
    # Enrich symbols already present in official lists; never let Yahoo ranking define discovery coverage.
    for screen in ("most_actives","day_gainers","day_losers"):
        try:
            d=get_json(SCREENER,{"formatted":"false","lang":"en-US","region":"US","scrIds":screen,"count":100,"corsDomain":"finance.yahoo.com"})
            for q in d.get("finance",{}).get("result",[{}])[0].get("quotes",[]):
                symbol=q.get("symbol")
                if symbol in found and q.get("quoteType") in (None,"EQUITY"): found[symbol].update(q)
        except Exception:
            pass
    return list(found.values())

def discovery_gate(drawdown, rebound, turnover, change, structural):
    """Discovery only: retain liquid sold-off names before a completed turn."""
    sold_off_watch=bool(drawdown<=-15 and 0<=rebound<=20 and turnover>=50_000_000)
    momentum_watch=bool(structural or (isinstance(change,(int,float)) and change>=1.0))
    return momentum_watch or sold_off_watch, sold_off_watch

def intraday_structure(rows):
    if len(rows)<18: return {"quality":False}
    # Work only with the latest trading date; timestamps are exchange-session bars.
    last_day=datetime.fromtimestamp(rows[-1]["ts"],timezone.utc).date() if rows[-1]["ts"] else None
    day=[r for r in rows if (datetime.fromtimestamp(r["ts"],timezone.utc).date() if r["ts"] else None)==last_day]
    if len(day)<18: day=rows[-120:]
    low_i=min(range(len(day)),key=lambda i:day[i]["low"]); low=day[low_i]["low"]
    after=day[low_i+1:]
    if len(after)<10: return {"quality":False,"day_low":low}
    # Split post-bottom path: first rebound then later pullback/continuation.
    peak_i=max(range(len(after)),key=lambda i:after[i]["high"])
    first_peak=after[peak_i]["high"]; later=after[peak_i+1:]
    if len(later)<4: return {"quality":False,"day_low":low,"first_rebound_high":first_peak}
    higher_low=min(r["low"] for r in later); price=day[-1]["close"]
    rebound=(first_peak/low-1)*100; hl_margin=(higher_low/low-1)*100
    reclaim=price>=first_peak*0.997
    # Path efficiency rejects wild V/chop: net progress relative to bar-to-bar travel.
    closes=[r["close"] for r in after]
    travel=sum(abs(b-a) for a,b in zip(closes,closes[1:]))
    efficiency=abs(closes[-1]-closes[0])/travel if travel else 0
    early=bool(rebound>=0.8 and hl_margin>=0.25 and efficiency>=0.12)
    quality=bool(early and reclaim)
    return {"quality":quality,"early_recovery_observed":early,"day_low":round(low,3),"first_rebound_high":round(first_peak,3),
            "higher_low":round(higher_low,3),"higher_low_margin_pct":round(hl_margin,2),
            "reclaim_observed":reclaim,"path_efficiency":round(efficiency,3)}

def main():
    now=datetime.now(timezone.utc); candidates=[]; failures={}
    for q in universe():
        symbol=q.get("symbol"); price=q.get("regularMarketPrice"); change=q.get("regularMarketChangePercent"); cap=q.get("marketCap")
        if not isinstance(price,(int,float)) or not isinstance(cap,(int,float)):
            try:
                probe=get_json(CHART+urllib.parse.quote(symbol),{"range":"1mo","interval":"1d"})["chart"]["result"][0]
                meta=probe.get("meta",{}); price=price if isinstance(price,(int,float)) else meta.get("regularMarketPrice")
                cap=cap if isinstance(cap,(int,float)) else meta.get("marketCap")
                pq=probe.get("indicators",{}).get("quote",[{}])[0]; closes=[x for x in pq.get("close",[]) if isinstance(x,(int,float))]
                highs=[x for x in pq.get("high",[]) if isinstance(x,(int,float))]
                vols=[x for x in pq.get("volume",[]) if isinstance(x,(int,float))]
                if price and highs and vols:
                    quick_dd=(min(closes[-20:])/max(highs)-1)*100 if closes else 0
                    quick_turn=price*(sum(vols[-20:])/max(1,len(vols[-20:])))
                    if quick_dd>-6 or quick_turn<35_000_000: continue
            except Exception:
                pass
        if not symbol or not isinstance(price,(int,float)) or price<1: continue
        if not isinstance(cap,(int,float)) or cap<2_000_000_000: continue
        try:
            daily=chart(symbol,"3mo","1d")
            if len(daily)<35: continue
            peak=max(x["high"] for x in daily[-60:]); trough=min(x["low"] for x in daily[-20:])
            drawdown=(trough/peak-1)*100; rebound=(price/trough-1)*100
            avgvol=sum(x["volume"] for x in daily[-21:-1])/max(1,len(daily[-21:-1])); turnover=price*avgvol
            # Discovery gate only: do not demand an execution-ready setup here.
            if drawdown>-8 or rebound<0 or rebound>35 or turnover<50_000_000: continue
            intra=intraday_structure(chart(symbol,"1d","1m"))
            structural=bool(intra.get("quality"))
            early=bool(intra.get("early_recovery_observed"))
            # Keep promising recovery names in discovery even before the intraday turn is complete.
            promising,sold_off_watch=discovery_gate(drawdown,rebound,turnover,change,structural)
            if not promising: continue
            candidates.append({"symbol":symbol,"name":q.get("shortName") or q.get("longName"),
              "status":"STRUCTURE-RECOGNISED" if structural else ("EARLY-RECOVERY-RESEARCH" if early else ("SOLD-OFF-RECOVERY-WATCH" if sold_off_watch else "DISCOVERY-WATCH")),
              "sold_off_recovery_watch":sold_off_watch,
              "structure_quality_pass":structural,"early_recovery_observed":early,"reference_price_usd":round(price,3),
              "day_change_pct":round(change,2) if isinstance(change,(int,float)) else None,
              "recent_peak_usd":round(peak,3),"recent_20d_trough_usd":round(trough,3),
              "recent_drawdown_pct":round(drawdown,2),"rebound_from_20d_trough_pct":round(rebound,2),
              "avg_20d_dollar_turnover_usd":round(turnover),"market_cap_usd":cap,
              "intraday_structure":intra,"route":"BOTTOM-HIGHER-LOW-RECLAIM",
              "execution_ready":False,
              "requires":["fresh broker structure","structural invalidation","company/news/event clearance","resistance map","DYNAMIC SIZING MONEY gate","R/R >= 2","portfolio fit","no chase"]})
        except Exception as exc: failures[symbol]=type(exc).__name__
    candidates.sort(key=lambda x:(not x["structure_quality_pass"],not x["early_recovery_observed"],-(x.get("day_change_pct") or 0),x["symbol"]))
    out={"generated_utc":now.isoformat(),"scope":"broad liquid US recovery discovery; structure recognition separated from execution; never automatic buy",
         "source":"Nasdaq Trader official Nasdaq + other-listed universe; Yahoo chart data for price/history/intraday; Yahoo ranked lists enrichment only",
         "candidate_count":len(candidates),"structure_count":sum(x["structure_quality_pass"] for x in candidates),
         "candidates":candidates[:30],"failures":failures}
    OUT.parent.mkdir(exist_ok=True); OUT.write_text(json.dumps(out,indent=2)); print(json.dumps(out,indent=2))
if __name__=="__main__": main()

