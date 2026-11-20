"""Research-only conservative sensitivity to uncertain future sell fees.

A user-supplied ceiling is a scenario assumption, not broker verification.
All outputs remain non-executable. No claim of worst-case market execution.
"""
import math
from research_net_scenario import evaluate_net_scenario

BLOCKED = {"trade_ready": False, "order_placement_enabled": False,
           "degiro_fee_verified": False,
           "source_authenticity_independently_verified": False}

def assess_sell_fee_uncertainty(*, sell_fee_estimate_eur, sell_fee_ceiling_eur,
                                scenario_inputs):
    if not isinstance(scenario_inputs, dict):
        return {**BLOCKED, "status": "SELL_FEE_UNCERTAINTY_BLOCKED",
                "reason": "INVALID_SCENARIO_INPUT"}
    if not all(type(v) in (int, float) and math.isfinite(v) and v >= 0
               for v in (sell_fee_estimate_eur, sell_fee_ceiling_eur)):
        return {**BLOCKED, "status": "SELL_FEE_UNCERTAINTY_BLOCKED",
                "reason": "INVALID_FEE_BOUNDS"}
    if sell_fee_ceiling_eur < sell_fee_estimate_eur:
        return {**BLOCKED, "status": "SELL_FEE_UNCERTAINTY_BLOCKED",
                "reason": "CEILING_BELOW_ESTIMATE"}
    if "sell_fee_eur" in scenario_inputs or "evidence_verified" in scenario_inputs:
        return {**BLOCKED, "status": "SELL_FEE_UNCERTAINTY_BLOCKED",
                "reason": "CONFLICTING_SCENARIO_FIELDS"}
    try:
        baseline = evaluate_net_scenario(**scenario_inputs,
                                         sell_fee_eur=sell_fee_estimate_eur,
                                         evidence_verified=False)
        conservative = evaluate_net_scenario(**scenario_inputs,
                                             sell_fee_eur=sell_fee_ceiling_eur,
                                             evidence_verified=False)
    except (TypeError, ValueError, OverflowError):
        return {**BLOCKED, "status": "SELL_FEE_UNCERTAINTY_BLOCKED",
                "reason": "INVALID_SCENARIO_FIELDS"}
    if "checks" not in baseline or "checks" not in conservative:
        return {**BLOCKED, "status": "SELL_FEE_UNCERTAINTY_BLOCKED",
                "reason": "SCENARIO_NOT_COMPUTABLE",
                "baseline_status": baseline["status"],
                "conservative_status": conservative["status"]}
    checks = conservative["checks"]
    qualified = (checks["net_profit_at_least_150_eur"] is True
                 and checks["net_rr_at_least_2"] is True)
    return {**BLOCKED, "status": ("CONSERVATIVE_RESEARCH_THRESHOLDS_MET"
                                  if qualified else "CONSERVATIVE_RESEARCH_THRESHOLDS_FAILED"),
            "baseline_net_profit_eur": baseline["net_profit_eur"],
            "baseline_net_rr": baseline["net_rr"],
            "conservative_net_profit_eur": conservative["net_profit_eur"],
            "conservative_net_rr": conservative["net_rr"],
            "sell_fee_estimate_eur": sell_fee_estimate_eur,
            "sell_fee_ceiling_eur": sell_fee_ceiling_eur,
            "sell_fee_ceiling_independently_verified": False,
            "note": "The ceiling is a hypothetical input, not a proven maximum fee."}
