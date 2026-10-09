#!/usr/bin/env python3
"""Build US PRE-ALERT handoff from deep recovery scan + broad fast recovery lane.
Research handoff only: never a buy signal and never broker verification.
"""
import json
from datetime import datetime, timezone
from pathlib import Path
SRC=Path("reports/us_batch_runs"); MOM=Path("reports/us_momentum_recovery.json"); OUT=Path("reports/us_auto_prealert_candidates.json")
rows=[]; seen=set()
for p in sorted(SRC.glob("batch_*.json")):
    try: report=json.loads(p.read_text())
    except Exception: continue
    for q in report.get("deep_dive_queue",[]):
        dossier=q.get("research_dossier") or {}; tri=q.get("research_triage") or {}; zones=q.get("pivot_zones") or []; symbol=q.get("symbol")
        last=dossier.get("historical_close_usd"); invalidation=dossier.get("historical_invalidation_reference_usd"); bottom_count=tri.get("bottom_signal_count")
        weekly_ok=bool(tri.get("weekly_close_rising") or tri.get("weekly_higher_low")); identity=(dossier.get("identity_crosscheck") or {}).get("status") or q.get("identity_status") or "IDENTITY_UNVERIFIED"; profile=(dossier.get("issuer_profile") or {}).get("status") or q.get("profile_status") or "UNVERIFIED"
        eligible=bool(symbol and bottom_count is not None and bottom_count>=3 and weekly_ok and zones and identity!="IDENTITY_MISMATCH")
        blocks=["LIVE-PROVIDER-TRIGGER-ROUTE-NOT-YET-DEFINED","BROKER-BID-ASK-NOT-VERIFIED","DYNAMIC-SIZING-MONEY-GATE-NOT-VERIFIED","FINAL-RR-EVENT-PORTFOLIO-GATES-PENDING"]
        if identity!="NAME_CONSISTENT_UNVERIFIED": blocks.insert(0,"ISSUER-IDENTITY-NOT-YET-CLEARED")
        rows.append({"symbol":symbol,"name":q.get("name"),"status":"PRE-ALERT" if eligible else "RESEARCH-ONLY","auto_promoted":eligible,"discovery_lane":"DEEP-RECOVERY","source":"current US recovery sweep","last_bar_date":q.get("last_bar_date"),"historical_close_usd":last,"bottom_signal_count":bottom_count,"space_to_first_overhead_pct":tri.get("space_to_first_overhead_pct"),"weekly_structure_support":weekly_ok,"identity_status":identity,"profile_status":profile,"historical_invalidation_reference_usd":invalidation,"historical_overhead_zones":zones[:3],"execution_ready":False,"execution_blocks":blocks})
        if symbol: seen.add(symbol)
if MOM.exists():
    try: mom=json.loads(MOM.read_text())
    except Exception: mom={}
    for c in mom.get("candidates",[]):
        s=c.get("symbol")
        if not s or s in seen: continue
        ref=c.get("reference_price_usd"); structural=bool(c.get("structure_quality_pass"))
        rows.append({"symbol":s,"name":c.get("name"),"status":"STRUCTURE-RECOGNISED" if structural else c.get("status","DISCOVERY-WATCH"),
          "auto_promoted":True,"structure_quality_pass":structural,"intraday_structure":c.get("intraday_structure"),
          "discovery_lane":"SOLD-OFF-RECOVERY" if c.get("sold_off_recovery_watch") and not structural else "FAST-MOMENTUM-RECOVERY","source":"market-wide official US equity universe recovery lane",
          "historical_close_usd":ref,"early_trigger_reference_usd":ref,"day_change_pct":c.get("day_change_pct"),
          "recent_drawdown_pct":c.get("recent_drawdown_pct"),"rebound_from_20d_trough_pct":c.get("rebound_from_20d_trough_pct"),
          "recent_20d_trough_usd":c.get("recent_20d_trough_usd"),"historical_invalidation_reference_usd":c.get("recent_20d_trough_usd"),
          "historical_overhead_zones":[],"execution_ready":False,
          "execution_blocks":["BROKER-BID-ASK-NOT-VERIFIED","COMPANY-NEWS-EVENT-CLEARANCE-PENDING","DYNAMIC-SIZING-MONEY-GATE-NOT-VERIFIED","R-R-2X-NOT-VERIFIED","PORTFOLIO-FIT-PENDING","NO-CHASE"]})
        seen.add(s)
out={"generated_utc":datetime.now(timezone.utc).isoformat(),"scope":"US deep recovery + broad fast recovery handoff; discovery and structure recognition separated from execution; never automatic buy","prealert_symbols":[x["symbol"] for x in rows if x.get("auto_promoted")],"rows":rows}
OUT.parent.mkdir(exist_ok=True); OUT.write_text(json.dumps(out,indent=2)); print(json.dumps(out,indent=2))

