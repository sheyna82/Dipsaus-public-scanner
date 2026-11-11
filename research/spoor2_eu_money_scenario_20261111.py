"""Isolated European whole-share EUR scenario; illustrative, never trade-ready.

Explicit bid/ask and exact GBp normalization. FX, fee and slippage inputs are
hypotheses until externally attested; no network, notifications or orders.
"""
from decimal import Decimal, InvalidOperation, ROUND_FLOOR, ROUND_HALF_UP
from research.spoor2_eu_quote_units_20261111 import normalize_quote

def _decimal(value, *, positive=False):
    if isinstance(value, bool) or not isinstance(value, (str, int, Decimal)):
        raise ValueError("invalid decimal")
    try:
        d = Decimal(str(value))
    except InvalidOperation as exc:
        raise ValueError("invalid decimal") from exc
    if not d.is_finite() or (d <= 0 if positive else d < 0):
        raise ValueError("out of range")
    return d

def european_money_scenario(*, quote_unit, ask, target_bid, invalidation,
                            budget_eur, eur_per_base_unit, buy_fee_eur,
                            sell_fee_eur, buy_fx_rate, sell_fx_rate,
                            buy_slippage="0", sell_slippage="0"):
    blocked = {"status": "BLOCKED", "trade_ready": False,
               "order_placement_enabled": False}
    a, t, i = (normalize_quote(v, quote_unit) for v in (ask, target_bid, invalidation))
    if any(x["status"] != "NORMALIZED_RESEARCH_ONLY" for x in (a, t, i)):
        return {**blocked, "blocks": ["QUOTE_UNIT_OR_PRICE_INVALID"]}
    try:
        ask_p, target_p, invalid_p = (Decimal(x["base_price"]) for x in (a, t, i))
        budget = _decimal(budget_eur, positive=True)
        fx = _decimal(eur_per_base_unit, positive=True)
        buy_fee = _decimal(buy_fee_eur)
        sell_fee = _decimal(sell_fee_eur)
        buy_rate = _decimal(buy_fx_rate)
        sell_rate = _decimal(sell_fx_rate)
        buy_slip = _decimal(buy_slippage)
        sell_slip = _decimal(sell_slippage)
    except ValueError:
        return {**blocked, "blocks": ["FINANCIAL_INPUT_INVALID"]}
    if buy_rate >= 1 or sell_rate >= 1:
        return {**blocked, "blocks": ["FX_FRICTION_INVALID"]}
    entry = ask_p + buy_slip
    exit_price = target_p - sell_slip
    if not (0 < invalid_p < entry < exit_price):
        return {**blocked, "blocks": ["PRICE_STRUCTURE_INVALID"]}
    cost_per_share = entry * fx * (1 + buy_rate)
    shares = int(((budget - buy_fee) / cost_per_share).to_integral_value(rounding=ROUND_FLOOR))
    if shares < 1:
        return {**blocked, "blocks": ["BUDGET_INSUFFICIENT"]}
    buy_total = shares * cost_per_share + buy_fee
    sell_total = shares * exit_price * fx * (1 - sell_rate) - sell_fee
    risk = entry - invalid_p
    rr = (exit_price - entry) / risk
    quantize = lambda x: str(x.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
    return {**blocked, "status": "ILLUSTRATIVE_NOT_VERIFIED",
            "blocks": ["FX_EXTERNAL_ATTESTATION_NOT_CONNECTED",
                       "BROKER_AND_TECHNICAL_LEVELS_NOT_INDEPENDENTLY_ATTESTED",
                       "FEES_AND_EXECUTION_NOT_VERIFIED"],
            "base_currency": a["base_currency"], "quote_unit": quote_unit,
            "whole_shares": shares, "purchase_eur": quantize(buy_total),
            "net_profit_eur": quantize(sell_total - buy_total),
            "reference_rr": str(rr.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)),
            "assumptions": "Static EUR FX, explicit ask/target bid, fixed fees and slippage; no live depth, FX movement or tax."}
