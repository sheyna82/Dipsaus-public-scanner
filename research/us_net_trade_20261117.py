"""Conservative broker-based EUR net trade research, never order-ready."""
import math
from research.us_level_evidence_20261117 import positive, fresh

def estimate_net_trade(broker, levels, fx, costs, tranche_eur=3500, now=None):
    required = ("ask", "bid", "checked_utc", "source", "verified")
    if not isinstance(broker, dict) or not all(k in broker for k in required):
        return {"status": "UNKNOWN", "blocks": ["BROKER_QUOTE_MISSING"], "trade_ready": False}
    if not broker["source"] or broker["verified"] is not True or not fresh(broker["checked_utc"], now, 120):
        return {"status": "UNKNOWN", "blocks": ["BROKER_QUOTE_UNVERIFIED_OR_STALE"], "trade_ready": False}
    if not all(positive(broker.get(k)) for k in ("ask", "bid")) or broker["bid"] > broker["ask"]:
        return {"status": "BLOCK", "blocks": ["BROKER_SPREAD_INVALID"], "trade_ready": False}
    if not isinstance(levels, dict) or levels.get("status") != "RESEARCH_LEVELS_VERIFIED":
        return {"status": "UNKNOWN", "blocks": ["LEVELS_NOT_VERIFIED"], "trade_ready": False}
    if not isinstance(fx, dict) or not positive(fx.get("eur_per_usd")) or not fx.get("source") or fx.get("verified") is not True or not fresh(fx.get("checked_utc"), now, 120):
        return {"status": "UNKNOWN", "blocks": ["EXECUTABLE_FX_NOT_VERIFIED"], "trade_ready": False}
    if not isinstance(costs, dict) or costs.get("verified") is not True:
        return {"status": "UNKNOWN", "blocks": ["COSTS_NOT_VERIFIED"], "trade_ready": False}
    keys = ("buy_fee_eur", "sell_fee_eur", "fx_cost_eur", "slippage_eur")
    if any(not isinstance(costs.get(k), (int, float)) or isinstance(costs.get(k), bool) or not math.isfinite(costs[k]) or costs[k] < 0 for k in keys):
        return {"status": "UNKNOWN", "blocks": ["COST_INPUT_INVALID"], "trade_ready": False}
    entry = broker["ask"]
    target, stop = levels["target"], levels["invalidation"]
    if not stop < entry < target:
        return {"status": "BLOCK", "blocks": ["UNFAVORABLE_STRUCTURE_AT_ASK"], "trade_ready": False}
    conversion = fx["eur_per_usd"]
    fees = sum(costs[k] for k in keys)
    shares = math.floor((tranche_eur - costs["buy_fee_eur"] - costs["fx_cost_eur"] - costs["slippage_eur"]) / (entry * conversion))
    if shares <= 0:
        return {"status": "BLOCK", "blocks": ["TRANCHE_INSUFFICIENT"], "trade_ready": False}
    gross = shares * (target - entry) * conversion
    net = gross - fees
    risk = shares * (entry - stop) * conversion + fees
    rr = net / risk if risk > 0 else 0
    blocks = []
    if rr < 2: blocks.append("RR_BELOW_2")
    if net < 150: blocks.append("NET_PROFIT_BELOW_150")
    return {"status": "RESEARCH_PASS" if not blocks else "RESEARCH_BLOCK",
            "shares": shares, "gross_profit_eur": round(gross, 2),
            "net_profit_eur": round(net, 2), "risk_eur": round(risk, 2),
            "rr": round(rr, 3), "blocks": blocks, "trade_ready": False,
            "note": "Research only: no news, events, portfolio, or broker route clearance"}
