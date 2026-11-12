"""Isolated, non-executable DIPSAUS research calculations (never an entry signal).

Historical pivots are *candidates*, not independently validated resistance.
A 10-day low is a *reference*, not automatically structural invalidation.
"""
import math


def _positive(value):
    return (isinstance(value, (int, float)) and not isinstance(value, bool)
            and math.isfinite(value) and value > 0)


def research_levels(recovery_map, reference_price):
    """Return transparent candidate levels, with all verification flags false."""
    if not _positive(reference_price) or not isinstance(recovery_map, dict):
        return {"status": "UNKNOWN", "trade_ready": False}
    zones = recovery_map.get("historical_overhead_pivot_zones") or []
    resistance = sorted({
        float(z["low_usd"]) for z in zones
        if isinstance(z, dict) and _positive(z.get("low_usd"))
        and z["low_usd"] > reference_price
    })
    invalidation = recovery_map.get("recent_10d_low_invalidation_reference_usd")
    if not _positive(invalidation) or invalidation >= reference_price:
        invalidation = None
    # Use the nearest overhead historical pivot conservatively, not the
    # most optimistic distant target. A candidate zone is never verified.
    zone = (research_entry_zone(
        broker_ask_usd=reference_price,
        invalidation_reference_usd=invalidation,
        resistance_reference_usd=resistance[0])
        if invalidation is not None and resistance else None)
    return {
        "entry_zone_research": zone,
        "status": "HISTORICAL_REFERENCES_ONLY",
        "entry_reference_usd": reference_price,
        "invalidation_reference_usd": invalidation,
        "resistance_references_usd": resistance,
        "required_2r_target_usd": round(reference_price + 2 * (reference_price - invalidation), 4)
            if invalidation is not None else None,
        "invalidation_verified": False,
        "resistance_verified": False,
        "broker_quote_verified": False,
        "trade_ready": False,
    }



def research_entry_zone(*, broker_ask_usd, invalidation_reference_usd,
                        resistance_reference_usd, minimum_rr=2):
    """Illustrative ask-to-ceiling zone at a reference R/R, never a signal.

    Solves (resistance - entry) / (entry - invalidation) >= minimum_rr.
    Ignores fees, spread changes, FX and slippage; source levels are unverified.
    """
    base = {"status": "UNKNOWN", "trade_ready": False,
            "entry_zone_verified": False, "order_placement_enabled": False}
    values = (broker_ask_usd, invalidation_reference_usd,
              resistance_reference_usd, minimum_rr)
    if not all(_positive(v) for v in values) or minimum_rr < 2:
        return base
    if not invalidation_reference_usd < broker_ask_usd < resistance_reference_usd:
        return base
    ceiling = ((resistance_reference_usd
                + minimum_rr * invalidation_reference_usd)
               / (1 + minimum_rr))
    if not math.isfinite(ceiling):
        return base
    if broker_ask_usd > ceiling:
        return {**base, "status": "REFERENCE_RR_BELOW_MINIMUM",
                "minimum_rr": minimum_rr, "entry_ceiling_reference_usd": ceiling}
    return {**base, "status": "ILLUSTRATIVE_ENTRY_ZONE_ONLY",
            "entry_zone_reference_usd": [broker_ask_usd, ceiling],
            "entry_ceiling_reference_usd": ceiling, "minimum_rr": minimum_rr,
            "limitations": "Unverified levels; ignores execution costs and changing quotes."}


def money_scenario(*, budget_eur, ask_usd, exit_bid_usd, invalidation_usd,
                   eur_per_usd, buy_fee_eur, sell_fee_eur, buy_fx_rate,
                   sell_fx_rate, slippage_buy_usd=0, slippage_sell_usd=0):
    """Whole-share illustrative scenario; no validated setup or order execution.

    FX rates are fractional costs per conversion (e.g. 0.0025 for 0.25%).
    Sell-side price is the executable *bid*, not the last trade.
    """
    fields = (budget_eur, ask_usd, exit_bid_usd, invalidation_usd,
              eur_per_usd, buy_fee_eur, sell_fee_eur, buy_fx_rate,
              sell_fx_rate, slippage_buy_usd, slippage_sell_usd)
    if any(not isinstance(x, (int, float)) or isinstance(x, bool)
           or not math.isfinite(x) for x in fields):
        return {"status": "UNKNOWN", "trade_ready": False}
    if not all(_positive(x) for x in (budget_eur, ask_usd, exit_bid_usd,
                                     invalidation_usd, eur_per_usd)):
        return {"status": "UNKNOWN", "trade_ready": False}
    if any(x < 0 for x in (buy_fee_eur, sell_fee_eur, buy_fx_rate, sell_fx_rate,
                          slippage_buy_usd, slippage_sell_usd)):
        return {"status": "UNKNOWN", "trade_ready": False}
    if buy_fx_rate >= 1 or sell_fx_rate >= 1:
        return {"status": "UNKNOWN", "trade_ready": False}
    entry = ask_usd + slippage_buy_usd
    exit_price = exit_bid_usd - slippage_sell_usd
    if not invalidation_usd < entry or exit_price <= 0:
        return {"status": "UNKNOWN", "trade_ready": False}
    unit_cost = entry * eur_per_usd * (1 + buy_fx_rate)
    shares = math.floor((budget_eur - buy_fee_eur) / unit_cost)
    if shares < 1:
        return {"status": "BUDGET_BLOCKED", "trade_ready": False}
    buy_total = shares * unit_cost + buy_fee_eur
    sell_total = shares * exit_price * eur_per_usd * (1 - sell_fx_rate) - sell_fee_eur
    risk_per_share = entry - invalidation_usd
    rr = (exit_price - entry) / risk_per_share
    return {
        "status": "ILLUSTRATIVE_NOT_VERIFIED",
        "whole_shares": shares,
        "purchase_eur": round(buy_total, 2),
        "net_profit_eur": round(sell_total - buy_total, 2),
        "reference_rr": round(rr, 4),
        "risk_eur_before_exit_friction": round(shares * risk_per_share * eur_per_usd, 2),
        "trade_ready": False,
        "limitations": "Historical levels unverified; FX movement, market depth, taxes and additional costs excluded.",
    }
