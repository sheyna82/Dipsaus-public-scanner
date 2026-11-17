"""Offline end-to-end US shadow evidence report.

Combines already isolated evidence gates; never turns a passing metadata
check into independent market-data, calendar, broker or trading authorization.
"""
from research.us_existing_handoff_audit_20261117 import audit_existing_us_handoff
from research.us_exchange_calendar_evidence_20261117 import review_exchange_calendar

def review_us_evidence_chain(discovery, handoff, routes, calendar_record, *,
                             session_date, now):
    chain=audit_existing_us_handoff(discovery,handoff,routes)
    calendar=review_exchange_calendar(calendar_record,session_date=session_date,now=now)
    blocks=list(chain["blocks"])+["CHAIN_"+b for b in calendar["blocks"]]
    for row in chain.get("rows",[]):
        for block in row["blocks"]:
            blocks.append("ROUTE_"+block)
    if not chain.get("provenance_complete"):
        blocks.append("END_TO_END_PROVENANCE_UNVERIFIED")
    if not calendar.get("exchange_calendar_verified"):
        blocks.append("OFFICIAL_EXCHANGE_CALENDAR_UNVERIFIED")
    blocks += ["INDEPENDENT_PRICE_SOURCE_UNVERIFIED",
               "BROKER_BID_ASK_UNVERIFIED",
               "EUR_NET_PROFIT_AND_RR_UNVERIFIED"]
    return {"status":"SHADOW_BLOCKED","blocks":sorted(set(blocks)),
            "route_count":len(chain.get("rows",[])),
            "provenance_complete":chain.get("provenance_complete",False),
            "calendar_verified":False,"trade_ready":False,"notify":False,
            "automatic_orders":False}
