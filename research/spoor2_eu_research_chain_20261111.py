"""Isolated EU evidence-to-scenario chain; fail-closed and never executable.

One immutable input mapping feeds both the evidence audit and illustrative
calculator. No user-supplied 'verified' flag can enable a trade or notification.
"""
from research.spoor2_eu_financial_evidence_20261111 import audit_eu_financial_inputs
from research.spoor2_eu_money_scenario_20261111 import european_money_scenario
from research.spoor2_eu_evidence_receipt_20261111 import build_eu_evidence_receipt
from research.spoor2_eu_receipt_verifier_20261111 import verify_eu_evidence_receipt

_REQUIRED = ("quote_unit", "ask", "target_bid", "invalidation", "budget_eur",
             "eur_per_base_unit", "buy_fee_eur", "sell_fee_eur",
             "buy_fx_rate", "sell_fx_rate")

def evaluate_eu_research_chain(candidate, *, now_utc):
    result = {"status": "BLOCKED", "trade_ready": False,
              "order_placement_enabled": False, "notification_channel": "NONE"}
    if not isinstance(candidate, dict):
        return {**result, "blocks": ["INVALID_CANDIDATE"]}
    missing = [key for key in _REQUIRED if key not in candidate]
    if missing:
        return {**result, "blocks": ["MISSING_FINANCIAL_INPUTS"], "missing_fields": missing}
    receipt = build_eu_evidence_receipt(candidate, captured_utc=now_utc)
    if receipt["status"] != "LOCAL_RECEIPT_ONLY":
        return {**result, "blocks": receipt["blocks"], "evidence_receipt": receipt}
    receipt_verification = verify_eu_evidence_receipt(candidate, receipt)
    if not receipt_verification["receipt_verified"]:
        return {**result, "blocks": receipt_verification["blocks"],
                "evidence_receipt": receipt,
                "receipt_verification": receipt_verification}
    audit = audit_eu_financial_inputs(candidate, now_utc=now_utc)
    args = {key: candidate[key] for key in _REQUIRED}
    args["buy_slippage"] = candidate.get("buy_slippage", "0")
    args["sell_slippage"] = candidate.get("sell_slippage", "0")
    scenario = european_money_scenario(**args)
    blocks = list(dict.fromkeys(audit["blocks"] + scenario.get("blocks", []) + receipt["blocks"] + receipt_verification["blocks"]))
    return {**result, "status": "RESEARCH_ONLY" if scenario["status"] == "ILLUSTRATIVE_NOT_VERIFIED" else "BLOCKED",
            "blocks": blocks, "evidence_audit": audit,
            "evidence_receipt": receipt,
            "receipt_verification": receipt_verification,
            "scenario": scenario, "notification_channel": "RESEARCH_PREVIEW_ONLY"}
