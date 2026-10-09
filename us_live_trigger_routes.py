#!/usr/bin/env python3
"""Build live monitoring routes for US PRE-ALERT candidates. Never a buy signal.

Discovery stays broad. Phone-alert eligibility is deliberately narrower: unreviewed
US discoveries remain in the route report as SILENT-FOLLOW rows, but cannot fire a
DEGIRO-CHECK notification until promoted in notification_quality_gate.json.
"""
import json
from datetime import datetime, timezone
from pathlib import Path

SRC=Path("reports/us_auto_prealert_candidates.json")
OUT=Path("reports/us_live_trigger_routes.json")
GATE=Path("config/notification_quality_gate.json")
data=json.loads(SRC.read_text()) if SRC.exists() else {"rows":[]}
try:
    gate=json.loads(GATE.read_text()) if GATE.exists() else {}
except Exception:
    gate={}
notify_watchlist=set(gate.get("auto_us_notify_watchlist",[]))
silent_follow=set(gate.get("auto_us_silent_follow",[]))
rows=[]

for x in data.get("rows",[]):
    if not x.get("auto_promoted"): continue
    symbol=x["symbol"]
    early=x.get("discovery_lane")=="FAST-MOMENTUM-RECOVERY"
    zones=x.get("historical_overhead_zones") or []; first=zones[0] if zones else None
    automatic_quality=bool(
        x.get("discovery_lane")=="DEEP-RECOVERY"
        and x.get("bottom_signal_count",0)>=4
        and x.get("weekly_structure_support")
        and x.get("identity_status")=="NAME_CONSISTENT_UNVERIFIED"
        and isinstance(x.get("space_to_first_overhead_pct"),(int,float))
        and x["space_to_first_overhead_pct"]>=3
    )
    phone_eligible=symbol in notify_watchlist or (automatic_quality and symbol not in silent_follow)
    if early:
        ref=x.get("early_trigger_reference_usd")
        z=[round(ref*0.995,3),round(ref*1.005,3)] if isinstance(ref,(int,float)) else None
        row={"symbol":symbol,"name":x.get("name"),"status":"EARLY-RECOVERY-PRE-ALERT" if phone_eligible else "SILENT-FOLLOW","route_type":"EARLY-MOMENTUM-RECOVERY-VERIFY" if phone_eligible else "REVIEWED-LATER-NO-PHONE","break_above_usd":ref if phone_eligible else None,"hold_zone_usd":z if phone_eligible else None,"reference_break_above_usd":ref,"reference_hold_zone_usd":z,"phone_notification_eligible":phone_eligible,"silent_follow":not phone_eligible,"historical_invalidation_reference_usd":x.get("historical_invalidation_reference_usd"),"source":"fast market-wide mover/recovery discovery; current price reference only","route_is_execution_signal":False,"requires":["fresh provider 1m structure","credible higher low or short consolidation/reclaim","fresh DEGIRO bid/ask + spread","current company/news/event clearance","structural invalidation","first friction + meaningful resistance + further recovery zone","portfolio fit","DYNAMIC SIZING MONEY gate","R/R >= 2","no chase"]}
    else:
        level=first.get("low_usd") if first else None; z=[first.get("low_usd"),first.get("high_usd")] if first else None
        row={"symbol":symbol,"name":x.get("name"),"status":"PRE-ALERT" if phone_eligible else "SILENT-FOLLOW","route_type":"BREAKOUT_RECLAIM_REFERENCE" if (first and phone_eligible) else "REVIEWED-LATER-NO-PHONE" if first else "DATA-BLOCKED","break_above_usd":level if phone_eligible else None,"hold_zone_usd":z if phone_eligible else None,"reference_break_above_usd":level,"reference_hold_zone_usd":z,"phone_notification_eligible":phone_eligible,"silent_follow":not phone_eligible,"historical_invalidation_reference_usd":x.get("historical_invalidation_reference_usd"),"source":"current US sweep historical pivot map","route_is_execution_signal":False,"requires":["fresh provider 1m quote","fresh DEGIRO bid/ask + spread","current daily/intraday structure review","event/news clearance","portfolio fit","DYNAMIC SIZING MONEY gate","R/R >= 2"]}
    if symbol in silent_follow:
        row["silent_follow_reason"]="Reviewed candidate: keep in reports/watch, but suppress phone noise until a materially better standalone setup is promoted."
    elif not phone_eligible:
        row["silent_follow_reason"]="New automatic discovery: keep broad discovery/reporting, but require review/promotion before urgent phone notification."
    row["auto_quality_promoted"]=automatic_quality
    rows.append(row)

out={"generated_utc":datetime.now(timezone.utc).isoformat(),"scope":"US PRE-ALERT live monitoring routes; broad discovery with selective phone escalation; never automatic buy","notification_gate":{"phone_watchlist":sorted(notify_watchlist),"rule":"Unreviewed automatic US discoveries are silent. Manual/portfolio watches are handled separately."},"rows":rows}
OUT.parent.mkdir(exist_ok=True); OUT.write_text(json.dumps(out,indent=2)); print(json.dumps(out,indent=2))

