"""Research-only DEGIRO evidence to EUR net scenario, with no trusted-source upgrade."""
from research_degiro_evidence import inspect_degiro_evidence
from research_degiro_metadata import inspect_broker_metadata_freshness
from research_net_scenario import evaluate_net_scenario
from research_technical_provenance import inspect_technical_level_claims
from research_fee_evidence_hierarchy import classify_fee_evidence

BLOCKED = {"trade_ready": False, "order_placement_enabled": False,
           "source_authenticity_independently_verified": False,
           "broker_route_verified": False, "degiro_fee_verified": False}

def evaluate_degiro_research_scenario(broker_evidence, technical, *, now,
                                     budget_eur=3500):
    """Never pass unverified broker assertions as evidence_verified=True."""
    gate = inspect_degiro_evidence(broker_evidence, now=now)
    if gate["status"] != "DEGIRO_CLAIMS_STRUCTURALLY_CONSISTENT":
        return {**BLOCKED, "status": "BROKER_EVIDENCE_BLOCKED",
                "reason": gate.get("reason")}
    if (broker_evidence.get("quote_instrument_isin") != broker_evidence["isin"]
            or broker_evidence.get("quote_operating_mic") != broker_evidence["operating_mic"]):
        return {**BLOCKED, "status": "QUOTE_IDENTITY_BLOCKED",
                "reason": "QUOTE_NOT_BOUND_TO_INSTRUMENT_VENUE"}
    metadata = inspect_broker_metadata_freshness(broker_evidence, now=now)
    if metadata["status"] != "BROKER_METADATA_CLAIMS_FRESH":
        return {**BLOCKED, "status": "BROKER_METADATA_BLOCKED",
                "reason": metadata.get("reason"), "group": metadata.get("group")}
    if (broker_evidence.get("instrument_currency") != "EUR"
            or broker_evidence.get("fee_currency") != "EUR"):
        return {**BLOCKED, "status": "CURRENCY_BLOCKED",
                "reason": "EUR_ONLY_RESEARCH_BRIDGE"}
    if (broker_evidence.get("fee_instrument_isin") != broker_evidence["isin"]
            or broker_evidence.get("fee_operating_mic") != broker_evidence["operating_mic"]
            or broker_evidence.get("fee_route_instrument_isin") != broker_evidence["route_instrument_isin"]
            or broker_evidence.get("fee_route_operating_mic") != broker_evidence["route_operating_mic"]):
        return {**BLOCKED, "status": "FEE_ROUTE_BINDING_BLOCKED",
                "reason": "FEE_CLAIM_NOT_BOUND_TO_INSTRUMENT_ROUTE"}
    fee_claim = broker_evidence.get("fee_evidence")
    if not isinstance(fee_claim, dict):
        return {**BLOCKED, "status": "FEE_EVIDENCE_BLOCKED",
                "reason": "MISSING_FEE_EVIDENCE"}
    fee_classification = classify_fee_evidence({
        **fee_claim, "isin": broker_evidence["isin"],
        "operating_mic": broker_evidence["operating_mic"]})
    if fee_classification["status"] not in (
            "PUBLIC_FEE_ASSUMPTION_ONLY", "UNAUTHENTICATED_ORDER_PREVIEW_CLAIM"):
        return {**BLOCKED, "status": "FEE_EVIDENCE_BLOCKED",
                "reason": fee_classification.get("reason")}
    if not isinstance(technical, dict) or any(
            key not in technical for key in ("invalidation", "target",
                                              "buy_slippage_per_share",
                                              "sell_slippage_per_share")):
        return {**BLOCKED, "status": "TECHNICAL_EVIDENCE_BLOCKED"}
    provenance = inspect_technical_level_claims(technical, broker_evidence, now=now)
    if provenance["status"] != "TECHNICAL_CLAIMS_STRUCTURALLY_CONSISTENT":
        return {**BLOCKED, "status": "TECHNICAL_PROVENANCE_BLOCKED",
                "reason": provenance.get("reason")}
    result = evaluate_net_scenario(
        ask=broker_evidence["quote_ask"], bid=broker_evidence["quote_bid"],
        invalidation=technical["invalidation"], target=technical["target"],
        budget_eur=budget_eur,
        buy_fee_eur=broker_evidence["fee_buy_eur"],
        sell_fee_eur=broker_evidence["fee_sell_eur"],
        fx_eur_per_unit=1, fx_buy_fee_rate=0, fx_sell_fee_rate=0,
        buy_slippage_per_share=technical["buy_slippage_per_share"],
        sell_slippage_per_share=technical["sell_slippage_per_share"],
        evidence_verified=False)
    if (fee_classification["status"] == "UNAUTHENTICATED_ORDER_PREVIEW_CLAIM"
            and result.get("shares") != fee_claim["preview_quantity"]):
        return {**BLOCKED, "status": "FEE_PREVIEW_QUANTITY_BLOCKED",
                "reason": "PREVIEW_QUANTITY_DIFFERS_FROM_SCENARIO"}
    checks = result.get("checks", {})
    financially_qualified = (checks.get("net_profit_at_least_150_eur") is True
                             and checks.get("net_rr_at_least_2") is True)
    status = ("UNAUTHENTICATED_RESEARCH_SCENARIO" if financially_qualified
              else result["status"])
    return {**result, **BLOCKED, "status": status,
            "fee_evidence_status": fee_classification["status"],
            "broker_claims_structurally_consistent": True,
            "source_note": "EUR-only hypothetical calculation; actual DEGIRO identity, route and fees unverified."}
