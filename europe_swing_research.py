"""DIPSAUS Europe historical recovery research: zones are hypotheses, never orders."""
import gzip,json,math,os,subprocess,tempfile
from collections import Counter
from datetime import datetime,timezone,date
from pathlib import Path
ROOT=Path("reports");ROOT.mkdir(exist_ok=True)
SOURCE=ROOT/"europe_ohlcv.jsonl.gz"
OUT=ROOT/"europe_swing_research.json"
def restore():
    if SOURCE.exists():return
    raise RuntimeError("DATA-BLOCKED: fresh EU database required")
def roundp(x):return round(x,4)
def pivots(bars):
    out=[]
    for i in range(2,len(bars)-2):
        h=bars[i][2]
        if all(h>bars[j][2] for j in (i-2,i-1,i+1,i+2)):out.append((i,h,bars[i][0]))
    return out
def zones(bars,entry):
    raw=[p for p in pivots(bars[-126:]) if p[1]>entry*1.007];clusters=[]
    for i,price,day in sorted(raw,key=lambda p:p[1]):
        hit=next((c for c in clusters if abs(price-c["level"])/c["level"]<=.018),None)
        if hit:hit["touches"]+=1;hit["level"]=(hit["level"]*(hit["touches"]-1)+price)/hit["touches"];hit["dates"].append(day)
        else:clusters.append({"level":price,"touches":1,"dates":[day]})
    return sorted(clusters,key=lambda c:c["level"])
def assess(record,now):
    sym=record["symbol"];currency=record.get("currency")
    bars=sorted({b[0]:b for b in record.get("bars",[]) if isinstance(b,list) and len(b)>=6}.values())
    row={"symbol":sym,"sector":record.get("sector"),"currency":currency,"exchange":record.get("exchange"),"trade_ready":False,"live_quote_verified":False,"fundamentals_verified":False,"news_verified":False,"portfolio_fit_verified":False,"fx_verified":currency=="EUR","research_only":True,"discovery_eligible":False}
    if len(bars)<150:return dict(row,status="DATA-BLOCKED",reason="Insufficient history",execution_blockers=["INSUFFICIENT-HISTORY"])
    close=bars[-1][4];last=bars[-1][0];peak=max(b[2] for b in bars[-126:]);age=(now.date()-date.fromisoformat(last)).days
    row.update(last_bar_date=last,calendar_days_old=age,bar_count=len(bars),historical_close=close,drawdown_126d_pct=roundp((close/peak-1)*100))
    if not close or close<=0:return dict(row,status="DATA-BLOCKED",reason="Invalid close",execution_blockers=["INVALID-CLOSE"])
    lows=[b[3] for b in bars];closes=[b[4] for b in bars];ma5=sum(closes[-5:])/5;ma20=sum(closes[-20:])/20
    sig={"higher_5d_low":min(lows[-5:])>min(lows[-20:-5]),"above_5d_ma":close>ma5,"ma5_rising":ma5>sum(closes[-10:-5])/5,"above_20d_ma":close>ma20,"three_pct_above_20d_low":close>=min(lows[-20:])*1.03}
    row.update(signals=sig,signal_count=sum(sig.values()))
    support=min(lows[-60:-5]);recent_low=min(lows[-20:]);recovery_low=min(lows[-10:]);invalidation=recovery_low
    row.update(historical_support_60d_ex_recent=roundp(support),historical_low_20d=roundp(recent_low),recovery_low_10d=roundp(recovery_low),indicative_invalidation_below=roundp(invalidation),invalidation_method="Lowest low of latest 10 daily bars; current recovery-leg reference",invalidation_note="Research reference only, NOT executable stop. Deeper 60d support is context, not automatically the R/R invalidation. Require current broker/retest validation before execution.")
    allzones=zones(bars,close);first=allzones[0] if allzones else None;meaningful=next((z for z in allzones if z["touches"]>=2),None);later=next((z for z in allzones if meaningful and z["level"]>meaningful["level"]*1.025 and z["touches"]>=2),None)
    def display(z):return {"price":roundp(z["level"]),"pivot_touches":z["touches"],"historical_dates":z["dates"]} if z else None
    row.update(first_friction=display(first),first_meaningful_resistance=display(meaningful),further_recovery_zone=display(later),zone_method="Historical 5-bar pivot-high clusters, +/-1.8%, >=2 touches for meaningful; not supply/volume verified")
    if currency=="EUR":
        units=3500/close
        row["historical_3500_eur_scenarios"]={"position_units_fractional_for_comparison":roundp(units),"first_friction_gross_eur":roundp(units*(first["level"]-close)) if first else None,"meaningful_resistance_gross_eur":roundp(units*(meaningful["level"]-close)) if meaningful else None,"further_zone_gross_eur":roundp(units*(later["level"]-close)) if later else None,"indicative_downside_eur":roundp(units*(close-invalidation)),"rr_to_meaningful":roundp((meaningful["level"]-close)/(close-invalidation)) if meaningful and close>invalidation else None,"rr_to_further":roundp((later["level"]-close)/(close-invalidation)) if later and close>invalidation else None,"note":"Historical illustration only: fractional shares, no fees, spread, FX, live execution or verified company risk."}
    else:row["historical_3500_eur_scenarios"]=None;row["money_gate_status"]="FX-BLOCKED: no validated current EUR conversion"
    flags=[]
    if age>4:flags.append("STALE-DATA")
    if row["signal_count"]<3:flags.append("BOTTOM-EVIDENCE-INSUFFICIENT")
    rr_meaningful=(meaningful["level"]-close)/(close-invalidation) if meaningful and close>invalidation else None;rr_further=(later["level"]-close)/(close-invalidation) if later and close>invalidation else None
    row["rr_gate_basis"]="First meaningful resistance is the primary gate; further zone may qualify only when independently supported and passage through first resistance remains plausible."
    if rr_meaningful is not None and rr_meaningful<2:
        flags.append("RR-BELOW-2-TO-1-AT-FIRST-MEANINGFUL; FURTHER-ZONE-REQUIRES-PASSAGE-VALIDATION" if rr_further is not None and rr_further>=2 else "RR-BELOW-2-TO-1")
    if currency=="EUR" and meaningful and row.get("historical_3500_eur_scenarios",{}).get("meaningful_resistance_gross_eur",0)<150:row["advisory_under_150_eur_reference"]=True
    if row["signal_count"]<2:flags.append("EARLY-BOTTOM-NOT-CONFIRMED")
    if row["drawdown_126d_pct"]>-20:row["depth_note"]="MODERATE-DRAWDOWN-NOT-A-BLOCKER"
    if not meaningful:flags.append("MEANINGFUL-RESISTANCE-UNRESOLVED")
    if not later:flags.append("FURTHER-ZONE-UNRESOLVED")
    # Discovery and execution are deliberately separate. Missing a farther zone or
    # incomplete bottom evidence must not erase a promising recovery from monitoring.
    discovery=bool(age<=4 and row["drawdown_126d_pct"]<=-10 and row["signal_count"]>=1)
    execution_blockers=[]
    if age>4:execution_blockers.append("STALE-DATA")
    if row["signal_count"]<2:execution_blockers.append("EARLY-BOTTOM-NOT-CONFIRMED")
    if not meaningful:execution_blockers.append("MEANINGFUL-RESISTANCE-UNRESOLVED")
    if currency!="EUR":execution_blockers.append("FX-UNVERIFIED")
    if rr_meaningful is None and not (rr_further is not None and rr_further>=2):execution_blockers.append("RR-UNRESOLVED")
    row.update(research_flags=flags,discovery_eligible=discovery,execution_blockers=execution_blockers,status="RECOVERY-DISCOVERY" if discovery else ("HISTORICAL-RESEARCH" if not flags else "RESEARCH-BLOCKED"))
    return row
def main():
    restore();records=[]
    with gzip.open(SOURCE,"rt",encoding="utf-8") as f:
        for line in f:
            if line.strip():records.append(json.loads(line))
    if not records:raise RuntimeError("Empty database")
    symbols=[r["symbol"] for r in records]
    if len(set(symbols))!=len(symbols):raise RuntimeError("Duplicate symbols in database")
    now=datetime.now(timezone.utc);rows=[assess(r,now) for r in records]
    report={"generated_utc":now.isoformat(),"source":"European expanded research universe, not market-wide","stored_symbols_examined":len(rows),"sector_counts":dict(Counter(r["sector"] for r in rows)),"last_bar_dates":dict(Counter(r.get("last_bar_date") for r in rows)),"statuses":dict(Counter(r["status"] for r in rows)),"discovery_eligible_count":sum(1 for r in rows if r.get("discovery_eligible")),"trade_ready_count":0,"full_europe_scanned":False,"live_quotes_verified":False,"warning":"Discovery eligibility is separate from execution readiness. Historical pivot zones are hypotheses. No current broker spread, news/events or portfolio check.","candidates":rows}
    OUT.write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding="utf-8");print(json.dumps({k:v for k,v in report.items() if k!="candidates"},indent=2))
if __name__=="__main__":main()

