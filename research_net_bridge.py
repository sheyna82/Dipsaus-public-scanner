"""Research-only bridge from existing US/EU evidence to net EUR scenarios.

Does not change production modules or infer missing broker quotes/costs.
"""
from research_net_scenario import evaluate_net_scenario


def evaluate_verified_research_evidence(evidence, *, market, budget_eur=3500):
    """Use explicitly verified broker data, structural levels and fee evidence.

    Both US and EU inputs use the same canonical field names; EUR instruments
    set fx_eur_per_unit=1 and zero FX conversion fee rates explicitly.
    """
    blocked = {"status": "DATA_BLOCKED", "trade_ready": False,
               "order_placement_enabled": False}
    if market not in ("US", "EU") or not isinstance(evidence, dict):
        return {**blocked, "reason": "INVALID_MARKET_OR_EVIDENCE"}
    required = ("broker_ask", "broker_bid", "invalidation", "target",
                "buy_fee_eur", "sell_fee_eur", "fx_eur_per_unit",
                "fx_buy_fee_rate", "fx_sell_fee_rate",
                "broker_quote_verified", "levels_verified",
                "fees_verified", "fx_verified", "quote_freshness_verified")
    missing = [key for key in required if evidence.get(key) is None]
    if missing:
        return {**blocked, "missing": missing}
    verification = ("broker_quote_verified", "levels_verified",
                    "fees_verified", "fx_verified", "quote_freshness_verified")
    unverified = [key for key in verification if evidence[key] is not True]
    if unverified:
        return {**blocked, "status": "REVIEW_BLOCKED",
                "unverified": unverified}
    return evaluate_net_scenario(
        ask=evidence["broker_ask"], bid=evidence["broker_bid"],
        invalidation=evidence["invalidation"], target=evidence["target"],
        budget_eur=budget_eur, buy_fee_eur=evidence["buy_fee_eur"],
        sell_fee_eur=evidence["sell_fee_eur"],
        fx_eur_per_unit=evidence["fx_eur_per_unit"],
        fx_buy_fee_rate=evidence["fx_buy_fee_rate"],
        fx_sell_fee_rate=evidence["fx_sell_fee_rate"],
        buy_slippage_per_share=evidence.get("buy_slippage_per_share", 0),
        sell_slippage_per_share=evidence.get("sell_slippage_per_share", 0),
        evidence_verified=True)
