"""Read-only, synthetic-safe audit of existing US discovery/handoff/route JSON.

Does not fill in missing provenance using report generation timestamps.
Never sends notifications or places orders.
"""
from datetime import datetime, timezone

def _aware(value):
    if not isinstance(value,str): return False
    try:
        x=datetime.fromisoformat(value.replace("Z","+00:00"))
        return x.tzinfo is not None
    except ValueError:
        return False

def audit_existing_us_handoff(discovery, handoff, routes):
    blocks=[]
    if not all(isinstance(x,dict) for x in (discovery,handoff,routes)):
        return {"status":"SHADOW_BLOCKED","blocks":["INPUT_DOCUMENT_INVALID"],
                "trade_ready":False,"notify":False,"automatic_orders":False}
    for label, doc in (("DISCOVERY",discovery),("HANDOFF",handoff),("ROUTES",routes)):
        if not _aware(doc.get("generated_utc")):
            blocks.append(label+"_GENERATED_TIME_UNRESOLVED")
        if not isinstance(doc.get("rows" if label!="DISCOVERY" else "candidates"),list):
            blocks.append(label+"_ROWS_UNRESOLVED")
    d={r.get("symbol"):r for r in discovery.get("candidates",[]) if isinstance(r,dict) and isinstance(r.get("symbol"),str)} if isinstance(discovery.get("candidates"),list) else {}
    h={r.get("symbol"):r for r in handoff.get("rows",[]) if isinstance(r,dict) and isinstance(r.get("symbol"),str)} if isinstance(handoff.get("rows"),list) else {}
    out=[]
    for route in routes.get("rows",[]) if isinstance(routes.get("rows"),list) else []:
        if not isinstance(route,dict) or not isinstance(route.get("symbol"),str):
            blocks.append("ROUTE_ROW_INVALID");continue
        sym=route["symbol"]
        hand=h.get(sym);source=d.get(sym)
        row_blocks=[]
        if hand is None:row_blocks.append("HANDOFF_SYMBOL_MISSING")
        if route.get("route_type")=="EARLY-MOMENTUM-RECOVERY-VERIFY" or (hand and hand.get("discovery_lane")=="FAST-MOMENTUM-RECOVERY"):
            if source is None:row_blocks.append("MOMENTUM_DISCOVERY_SYMBOL_MISSING")
        if not hand or not _aware(hand.get("discovery_observed_utc")):
            row_blocks.append("DISCOVERY_OBSERVATION_TIME_MISSING")
        if not hand or not _aware(hand.get("source_daily_last_bar_utc")):
            row_blocks.append("SOURCE_DAILY_TIMESTAMP_MISSING")
        if not hand or not _aware(hand.get("source_intraday_last_bar_utc")):
            row_blocks.append("SOURCE_INTRADAY_TIMESTAMP_MISSING")
        if not isinstance(route.get("pivot_origin_session_date"),str):
            row_blocks.append("PIVOT_ORIGIN_DATE_MISSING")
        if not isinstance(route.get("source_observation_utc"),str):
            row_blocks.append("ROUTE_SOURCE_OBSERVATION_MISSING")
        out.append({"symbol":sym,"blocks":sorted(set(row_blocks)),"provenance_complete":not row_blocks})
    return {"status":"SHADOW_BLOCKED","blocks":sorted(set(blocks)),
            "rows":out,"provenance_complete":bool(out) and not blocks and all(x["provenance_complete"] for x in out),
            "trade_ready":False,"notify":False,"automatic_orders":False}
