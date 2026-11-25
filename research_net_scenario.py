"""Research-only net EUR scenario calculator. Never authorizes orders.

All inputs are independently supplied hypothetical or verified evidence.
No price targets or invalidations are inferred by this module.
"""
from fractions import Fraction
import math
import sys


MAX_FINITE = Fraction(sys.float_info.max)


def _number(value, *, allow_zero=False):
    if type(value) not in (int, float):
        return False
    try:
        return math.isfinite(value) and (value >= 0 if allow_zero else value > 0)
    except (OverflowError, ValueError):
        return False


def evaluate_net_scenario(*, ask, bid, invalidation, target, budget_eur,
                          buy_fee_eur, sell_fee_eur, fx_eur_per_unit=1.0,
                          buy_slippage_per_share=0.0,
                          sell_slippage_per_share=0.0,
                          evidence_verified=False, fx_buy_fee_rate=0.0,
                          fx_sell_fee_rate=0.0, max_risk_eur=None):
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
             sell_slippage_per_share, fx_buy_fee_rate,
             fx_sell_fee_rate)
    if not all(_number(v) for v in values) or not all(
            _number(v, allow_zero=True) for v in costs):
        return {**blocked, "status": "INVALID_OR_MISSING_INPUT"}
    # Treat decimal prices and fees as entered and keep the boundary comparisons exact.
    if max_risk_eur is not None and not _number(max_risk_eur):
        return {**blocked, 'status': 'INVALID_OR_MISSING_INPUT'}
    ask, bid, invalidation, target, budget_eur, fx_eur_per_unit = (
        Fraction(str(value)) for value in values)
    (buy_fee_eur, sell_fee_eur, buy_slippage_per_share, sell_slippage_per_share,
     fx_buy_fee_rate, fx_sell_fee_rate) = (Fraction(str(value)) for value in costs)
    if not (invalidation < bid <= ask < target):
        return {**blocked, "status": "STRUCTURE_BLOCKED"}
    entry = ask + buy_slippage_per_share
    exit_target = target - sell_slippage_per_share
    exit_stop = invalidation - sell_slippage_per_share
    if not (0 < exit_stop < entry < exit_target):
        return {**blocked, "status": "FRICTION_BLOCKED"}
    buy_unit_eur = entry * fx_eur_per_unit * (1 + fx_buy_fee_rate)
    if not 0 < buy_unit_eur <= MAX_FINITE:
        return {**blocked, "status": "NUMERIC_OVERFLOW_BLOCKED"}
    units_affordable = (budget_eur - buy_fee_eur) / buy_unit_eur
    if abs(units_affordable) > MAX_FINITE:
        return {**blocked, "status": "NUMERIC_OVERFLOW_BLOCKED"}
    quantity = math.floor(units_affordable)
    if quantity < 1:
        return {**blocked, "status": "BUDGET_BLOCKED"}
    entry_total = quantity * buy_unit_eur + buy_fee_eur
    target_total = quantity * exit_target * fx_eur_per_unit * (1 - fx_sell_fee_rate) - sell_fee_eur
    stop_total = quantity * exit_stop * fx_eur_per_unit * (1 - fx_sell_fee_rate) - sell_fee_eur
    if not all(abs(v) <= MAX_FINITE for v in (entry_total, target_total, stop_total)):
        return {**blocked, "status": "NUMERIC_OVERFLOW_BLOCKED"}
    net_profit = target_total - entry_total
    net_risk = entry_total - stop_total
    if not all(abs(v) <= MAX_FINITE for v in (net_profit, net_risk)):
        return {**blocked, "status": "NUMERIC_OVERFLOW_BLOCKED"}
    if net_risk <= 0:
        return {**blocked, "status": "INVALID_RISK"}
    net_rr = net_profit / net_risk
    if abs(net_rr) > MAX_FINITE:
        return {**blocked, "status": "NUMERIC_OVERFLOW_BLOCKED"}
    checks = {"net_profit_at_least_150_eur": net_profit >= 150,
              "net_rr_at_least_2": net_profit >= 2 * net_risk,
              "evidence_verified": evidence_verified is True}
    if max_risk_eur is not None:
        checks["net_risk_within_cap"] = net_risk <= Fraction(str(max_risk_eur))
    return {**blocked,
            "status": ("HUMAN_REVIEW_REQUIRED" if all(checks.values())
                       else "RESEARCH_ONLY_BLOCKED"),
            "shares": quantity,
            "notional_with_buy_fee_eur": float(round(entry_total, 2)),
            "net_profit_eur": float(round(net_profit, 2)),
            "net_risk_eur": float(round(net_risk, 2)),
            "net_rr": float(round(net_rr, 4)),
            "checks": checks,
            "limitations": "FX fee rates must be verified externally; no liquidity, source freshness, news, portfolio or broker route verification; never executable."}
