#!/usr/bin/env python3
"""Evaluate manual recovery triggers against a fresh provider quote.

Monitoring/pre-alert layer only. Config routes may evolve per ticker; unsupported
or broker-only routes are skipped here instead of crashing the whole watch.
"""
import json
from datetime import datetime, timezone
from pathlib import Path
import yfinance as yf

CONFIG=Path("config/manual_recovery_triggers.json")
SUPPLEMENTAL_CONFIG=Path("config/manual_recovery_triggers_supplemental.json")
OUT=Path("reports/manual_recovery_trigger_report.json")
US_ROUTES=Path("config/us_live_trigger_routes.json")
MAX_AGE_SECONDS=120

def latest_quote(symbol):
    t=yf.Ticker(symbol); h=t.history(period="1d",interval="1m",prepost=False)
    if h.empty: return None,None
    idx=h.index[-1]
    if getattr(idx,"tzinfo",None) is None: idx=idx.tz_localize("UTC")
    return float(h["Close"].iloc[-1]),idx.tz_convert("UTC").to_pydatetime()

def zone(route,*keys):
    if not isinstance(route,dict): return None
    for k in keys:
        z=route.get(k)
        if isinstance(z,list) and len(z)==2 and all(v is not None for v in z): return z
    return None

cfg=json.loads(CONFIG.read_text())
if SUPPLEMENTAL_CONFIG.exists():
    extra=json.loads(SUPPLEMENTAL_CONFIG.read_text())
    cfg.setdefault("candidates",{}).update(extra.get("candidates",{}))
now=datetime.now(timezone.utc); rows=[]
for symbol,item in cfg.get("candidates",{}).items():
    try:
        price,ts=latest_quote(symbol)
    except Exception as exc:
        rows.append({"symbol":symbol,"status":"DATA-BLOCKED","error":type(exc).__name__,"execution_ready":False})
        continue
    age=(now-ts).total_seconds() if ts else None
    fresh=bool(age is not None and -30<=age<=MAX_AGE_SECONDS)
    r1=item.get("route_1_retest") or {}
    r2=item.get("route_2_breakout") or item.get("route_2_old_reclaim_context") or {}
    z1=zone(r1,"zone_eur","zone_usd"); z2=zone(r2,"hold_zone_eur","hold_zone_usd")
    level=r2.get("break_above_eur",r2.get("break_above_usd"))
    provider_currency = item.get("currency")
    broker_currency = item.get("broker_currency")
    cross_currency_block = bool(broker_currency and provider_currency and broker_currency != provider_currency)
    if item.get("provider_symbol") and item.get("broker_listing") and broker_currency == "EUR": cross_currency_block=True
    touch=bool(not cross_currency_block and price is not None and z1 and z1[0]<=price<=z1[1])
    breakout=bool(not cross_currency_block and price is not None and level is not None and price>level)
    hold=bool(not cross_currency_block and price is not None and z2 and z2[0]<=price<=z2[1])
    # A quote touching a research level is NOT proof of a holding higher low,
    # consolidation, structural invalidation, broker spread or viable money/RR.
    # Keep research-only routes silent until those checks can be made.
    research_only=bool(item.get("monitor_mode") or "NOT-BUY-READY" in item.get("status",""))
    if item.get("provisional_retest_zone_usd") and item.get("first_meaningful_resistance_zone_usd"):
        z1 = zone(item,"provisional_retest_zone_usd")
        level = float(item["first_meaningful_resistance_zone_usd"][1])
        touch=bool(not cross_currency_block and price is not None and z1 and z1[0]<=price<=z1[1])
        breakout=bool(not cross_currency_block and price is not None and price>level)
        hold=False
    observed=bool(fresh and not cross_currency_block and (touch or breakout or hold))
    trigger=bool(observed and not research_only)
    status="BROKER-CHECK-CANDIDATE" if cross_currency_block and fresh else "RESEARCH-LEVEL-TOUCHED" if observed and research_only else "DEGIRO-VERIFY-NOW" if trigger else "WATCH"
    blocks=["NOT-AUTOMATIC-BUY","FINAL-DIPSAUS-GATES-PENDING"]
    if research_only:
        blocks.extend(["RESEARCH-ONLY-NO-PHONE-PREALERT","HIGHER-LOW-OR-HOLD-UNVERIFIED","FIRST-RESISTANCE-AND-RR-UNVERIFIED","EUR-GROSS-PROFIT-UNVERIFIED","BROKER-SPREAD-AND-PORTFOLIO-FIT-UNVERIFIED"])
    if cross_currency_block: blocks.append("CROSS-CURRENCY-LISTING-NUMERIC-COMPARISON-BLOCKED")
    rows.append({"symbol":symbol,"provider_quote":price,"provider_quote_utc":ts.isoformat() if ts else None,"provider_quote_age_seconds":age,"provider_freshness_pass":fresh,"route_1_zone":z1,"route_1_touch_observed":touch,"route_2_break_above":level,"route_2_hold_zone":z2,"route_2_break_observed":breakout,"route_2_hold_zone_observed":hold,"cross_currency_listing_block":cross_currency_block,"dynamic_route_present":bool(item.get("route_1_pullback_turn") or item.get("route_1_intraday_turn")),"research_level_observed":observed,"research_only":research_only,"prealert_trigger_observed":trigger,"status":status,"execution_ready":False,"mandatory_final_checks":["RECENT-PRICE-MOVING-NEWS","UPCOMING-MATERIAL-EVENTS","BROKER-BID-ASK","MONEY-RR","PORTFOLIO-FIT"],"execution_blocks":blocks})

PORTFOLIO=Path("config/portfolio_reentry_watch.json")
if PORTFOLIO.exists():
  try:
    pcfg=json.loads(PORTFOLIO.read_text()); rules=pcfg.get("early_reentry",{})
    min_drop=float(rules.get("min_intraday_drop_pct",3)); min_day_rebound=float(rules.get("min_rebound_from_day_low_pct",1)); recent_n=int(rules.get("recent_window_minutes",20)); min_recent_rebound=float(rules.get("min_rebound_from_recent_low_pct",.6))
    br=rules.get("base_test",{}); base_enabled=bool(br.get("enabled",True)); base_min_drop=float(br.get("min_intraday_drop_pct",1.5)); base_max_dist=float(br.get("max_distance_from_5d_low_pct",4)); base_min_vol=float(br.get("min_recent_volume_ratio",1.5)); base_min_rebound=float(br.get("min_recent_rebound_pct",.35)); base_min_range=float(br.get("min_selloff_range_pct",1.5))
    for symbol,item in pcfg.get("candidates",{}).items():
      try:
        h=yf.Ticker(symbol).history(period="5d",interval="1m",prepost=False)
      except Exception as exc:
        rows.append({"symbol":symbol,"watch_type":"PORTFOLIO-REENTRY","status":"DATA-BLOCKED","error":type(exc).__name__,"execution_ready":False})
        continue
      if h.empty: rows.append({"symbol":symbol,"watch_type":"PORTFOLIO-REENTRY","status":"DATA-BLOCKED","execution_ready":False}); continue
      dates=h.index.date; d=dates[-1]; day=h[[x==d for x in dates]]; prior=h[[x<d for x in dates]]
      if day.empty or prior.empty: continue
      prev=float(prior["Close"].iloc[-1]); price=float(day["Close"].iloc[-1]); low=float(day["Low"].min()); recent=day.tail(max(3,recent_n)); rlow=float(recent["Low"].min()); change=(price/prev-1)*100; rebound=(price/low-1)*100; rrebound=(price/rlow-1)*100
      idx=day.index[-1]; idx=idx.tz_localize("UTC") if getattr(idx,"tzinfo",None) is None else idx; ts=idx.tz_convert("UTC").to_pydatetime(); age=(now-ts).total_seconds(); fresh=-30<=age<=MAX_AGE_SECONDS
      five=float(h["Low"].min()); reb5=(price/five-1)*100; closes=recent["Close"]; lows=recent["Low"]; half=max(2,len(recent)//2); a=float(lows.iloc[:half].min()); b=float(lows.iloc[half:].min()) if len(lows.iloc[half:]) else a; higher=b>a; reclaim=len(closes)>=4 and price>float(closes.iloc[:-1].median())
      dip=change<=-min_drop and rebound>=min_day_rebound and rrebound>=min_recent_rebound; multi=reb5>=max(1.5,min_day_rebound) and higher and reclaim and rrebound>=min_recent_rebound
      dist=(price/five-1)*100; high=float(day["High"].max()); rng=(high/low-1)*100 if low else 0; vols=day["Volume"].astype(float); rv=recent["Volume"].astype(float); base=vols.iloc[:-len(rv)] if len(vols)>len(rv) else vols; bn=base[base>0]; rn=rv[rv>0]; bv=float(bn.median()) if len(bn) else 0; rvm=float(rn.median()) if len(rn) else 0; vr=rvm/bv if bv>0 else 0; stab=higher or reclaim or rrebound>=base_min_rebound; basetest=base_enabled and change<=-base_min_drop and dist<=base_max_dist and vr>=base_min_vol and rng>=base_min_range and stab
      early=dip or multi or basetest; trig=fresh and early; route="ACTIVE-HOLDING-DIP-TURN" if dip else "ACTIVE-HOLDING-MULTIDAY-RECOVERY" if multi else "ACTIVE-HOLDING-BASE-TEST" if basetest else None
      rows.append({"symbol":symbol,"name":item.get("name"),"watch_type":"PORTFOLIO-REENTRY","provider_quote":price,"provider_quote_utc":ts.isoformat(),"provider_quote_age_seconds":age,"provider_freshness_pass":fresh,"day_change_pct":round(change,3),"day_low":low,"rebound_from_day_low_pct":round(rebound,3),"recent_low":rlow,"rebound_from_recent_low_pct":round(rrebound,3),"five_day_low":five,"rebound_from_5d_low_pct":round(reb5,3),"higher_low_observed":higher,"recent_reclaim_observed":reclaim,"recent_volume_ratio":round(vr,3),"base_test_observed":basetest,"prealert_trigger_observed":trig,"triggered_route":route,"status":"LOOK-NOW" if basetest and not(dip or multi) else "DEGIRO-VERIFY-NOW" if trig else "WATCH","execution_ready":False,"mandatory_final_checks":["FRESH-DEGIRO-CHART","BROKER-BID-ASK","STRUCTURAL-INVALIDATION","RECENT-PRICE-MOVING-NEWS","UPCOMING-MATERIAL-EVENTS","MONEY-RR","PORTFOLIO-FIT"],"execution_blocks":["NOT-AUTOMATIC-BUY","NEW-SETUP-MUST-STAND-ALONE","FINAL-DIPSAUS-GATES-PENDING"]})
  except Exception as exc: rows.append({"symbol":"PORTFOLIO-WATCH","watch_type":"PORTFOLIO-REENTRY","status":"DATA-BLOCKED","error":type(exc).__name__,"execution_ready":False})

if US_ROUTES.exists():
  try:
    us=json.loads(US_ROUTES.read_text())
    for item in us.get("rows",[]):
      symbol=item.get("symbol")
      try:
        price,ts=latest_quote(symbol)
      except Exception as exc:
        rows.append({"symbol":symbol,"market":"US","status":"DATA-BLOCKED","error":type(exc).__name__,"execution_ready":False})
        continue
      age=(now-ts).total_seconds() if ts else None; fresh=bool(age is not None and -30<=age<=MAX_AGE_SECONDS); level=item.get("break_above_usd"); z=item.get("hold_zone_usd") or [None,None]; breakout=bool(price is not None and level is not None and price>level); hold=bool(price is not None and z[0] is not None and z[0]<=price<=z[1]); trig=fresh and bool(item.get("phone_notification_eligible")) and (breakout or hold)
      rows.append({"symbol":symbol,"market":"US","watch_type":"AUTO-US-DISCOVERY","phone_notification_eligible":bool(item.get("phone_notification_eligible")),"provider_quote":price,"provider_quote_utc":ts.isoformat() if ts else None,"provider_quote_age_seconds":age,"provider_freshness_pass":fresh,"route_2_break_above":level,"route_2_hold_zone":z,"breakout_observed":breakout,"hold_observed":hold,"prealert_trigger_observed":trig,"status":"DEGIRO-VERIFY-NOW" if trig else "WATCH","execution_ready":False})
  except Exception as exc: rows.append({"symbol":"US-ROUTES","status":"DATA-BLOCKED","error":type(exc).__name__,"execution_ready":False})
report={"generated_utc":now.isoformat(),"scope":"Europe/US recovery trigger watch; monitoring only; never automatic buy.","rows":rows}
OUT.parent.mkdir(parents=True,exist_ok=True); OUT.write_text(json.dumps(report,indent=2)); print(json.dumps(report,indent=2))

