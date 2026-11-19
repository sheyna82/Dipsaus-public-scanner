"""Join independent evidence without modifying notifications or trading gates."""
from research.us_level_evidence_20261117 import assess_levels
from research.us_trend_context_20261117 import assess_trend
from research.us_net_trade_20261117 import estimate_net_trade

def assess_candidate(data, now=None):
    levels = assess_levels(data.get("quote"), data.get("resistance"), data.get("invalidation"), now)
    trend = assess_trend(data.get("timeframes"), now)
    money = estimate_net_trade(data.get("broker"), levels, data.get("fx"), data.get("costs"),
                               data.get("tranche_eur", 3500), now)
    blocks = list(levels.get("blocks", [])) + list(money.get("blocks", []))
    if trend["status"] != "MULTITIMEFRAME_CONFIRMED":
        blocks.append("MULTITIMEFRAME_NOT_CONFIRMED")
    for field in ("news_verified", "events_verified", "portfolio_fit_verified",
                  "instrument_verified", "broker_route_verified"):
        if data.get(field) is not True:
            blocks.append(field.upper() + "_MISSING")
    research_pass = not blocks and money["status"] == "RESEARCH_PASS"
    return {"symbol": data.get("symbol"), "status": "RESEARCH_CANDIDATE" if research_pass else "INCOMPLETE_OR_BLOCKED",
            "levels": levels, "trend": trend, "money": money, "blocks": sorted(set(blocks)),
            "trade_ready": False, "notify": False, "automatic_orders": False,
            "mode": "SHADOW_RESEARCH_ONLY"}
