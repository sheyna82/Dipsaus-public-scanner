"""Research-only net EUR scenario calculator. Never authorizes orders.

All inputs are independently supplied hypothetical or verified evidence.
No price targets or invalidations are inferred by this module.
"""
import math


def _number(value, *, allow_zero=False):
    return (type(value) in (int, float) and math.isfinite(value)
            and (value >= 0 if allow_zero else value > 0))


def evaluate_net_scenario(*, ask, bid, invalidation, target, budget_eur,
                          buy_fee_eur, sell_fee_eur, fx_eur_per_unit=1.0,
                          buy_slippage_per_share=0.0,
                          sell_slippage_per_share=0.0,
                          evidence_verified=False):
    """Fail closed on absent fees, invalid structure or unverified evidence.

    ask/bid/target/invalidation/slippage are in the instrument currency.
    FX is EUR per instrument-currency unit. Sell proceeds use the target
    less sell slippage; invalidation proceeds use invalidation less sell
    slippage. Entry uses ask plus buy slippage. No automatic orders.
    """
    blocked = {"trade_ready": False, "order_placement_enabled": False}
    values = (ask, bid, invalidation, target, budget_eur,
              fx_eur_per_unit)
    costs = (buy_fee_eur, sell_fee_eur, buy_slippage_per_share,
             sell_slippage_per_share)
    if not all(_number(v) for v in values) or not all(
            _number(v, allow_zero=True) for v in costs):
        return {**blocked, "status": "INVALID_OR_MISSING_INPUT"}
    if not (invalidation < bid <= ask < target):
        return {**blocked, "status": "STRUCTURE_BLOCKED"}
    entry = ask + buy_slippage_per_share
    exit_target = target - sell_slippage_per_share
    exit_stop = invalidation - sell_slippage_per_share
    if not (0 < exit_stop < entry < exit_target):
        return {**blocked, "status": "FRICTION_BLOCKED"}
    quantity = math.floor((budget_eur - buy_fee_eur) /
                          (entry * fx_eur_per_unit))
    if quantity < 1:
        return {**blocked, "status": "BUDGET_BLOCKED"}
    roundtrip = buy_fee_eur + sell_fee_eur
    net_profit = quantity * (exit_target - entry) * fx_eur_per_unit - roundtrip
    net_risk = quantity * (entry - exit_stop) * fx_eur_per_unit + roundtrip
    net_rr = net_profit / net_risk
    checks = {"net_profit_at_least_150_eur": net_profit >= 150,
              "net_rr_at_least_2": net_rr >= 2,
              "evidence_verified": evidence_verified is True}
    return {**blocked,
            "status": ("HUMAN_REVIEW_REQUIRED" if all(checks.values())
                       else "RESEARCH_ONLY_BLOCKED"),
            "shares": quantity,
            "notional_with_buy_fee_eur": round(
                quantity * entry * fx_eur_per_unit + buy_fee_eur, 2),
            "net_profit_eur": round(net_profit, 2),
            "net_risk_eur": round(net_risk, 2),
            "net_rr": round(net_rr, 4),
            "checks": checks,
            "limitations": "No liquidity, source freshness, news, portfolio or broker route verification; never executable."}
