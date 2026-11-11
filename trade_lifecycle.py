"""DIPSAUS research-only trade lifecycle. No quotes fetched and no orders sent.

All monetary amounts are EUR. Inputs must be verified externally, including
broker fills, FX, liquidity, event calendar and completed-candle timestamps.
"""
from dataclasses import dataclass
from math import floor, isfinite


def _number(value, name):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not isfinite(value):
        raise ValueError(name + " must be finite")
    return float(value)


def portfolio_risk(positions, *, max_total_eur=300.0, max_sector_eur=150.0):
    """Conservative sum of planned stop risks, NOT guaranteed loss in gaps."""
    total = 0.0
    by_sector = {}
    for p in positions:
        risk = _number(p["planned_risk_eur"], "planned_risk_eur")
        if risk < 0:
            raise ValueError("Negative risk")
        sector = str(p.get("sector") or "UNKNOWN")
        total += risk
        by_sector[sector] = by_sector.get(sector, 0.0) + risk
    blockers = []
    if total > max_total_eur:
        blockers.append("PORTFOLIO_RISK_LIMIT")
    if any(v > max_sector_eur for v in by_sector.values()):
        blockers.append("SECTOR_RISK_LIMIT")
    return {"planned_total_risk_eur": round(total, 2),
            "sector_risk_eur": {k: round(v, 2) for k, v in by_sector.items()},
            "blockers": blockers, "risk_is_guaranteed": False}


def profit_protection(*, entry, current, peak, shares, reference_stop=None,
                      giveback_warning_fraction=0.35,
                      giveback_urgent_fraction=0.60,
                      confirmed_trend_break=False, rapid_crash=False,
                      fresh_data=False, broker_verified=False):
    """A rising position gets graduated warnings, not automatic exits.

    Profit is marked-to-market and excludes spread, commissions and FX.
    Peak must be a verified post-entry peak in the same currency/listing.
    A normal pullback alone never becomes a confirmed trend break.
    """
    entry, current, peak = (_number(x, n) for x, n in
                            ((entry, "entry"), (current, "current"), (peak, "peak")))
    if not isinstance(shares, int) or isinstance(shares, bool) or shares <= 0:
        raise ValueError("shares must be positive whole number")
    if entry <= 0 or current <= 0 or peak < max(entry, current):
        raise ValueError("Invalid entry/current/peak")
    if not (0 < giveback_warning_fraction < giveback_urgent_fraction < 1):
        raise ValueError("Invalid giveback fractions")
    if reference_stop is not None:
        reference_stop = _number(reference_stop, "reference_stop")
        if not 0 <= reference_stop < current:
            raise ValueError("Reference stop must be below current price")
    peak_profit = max(0.0, (peak - entry) * shares)
    current_profit = (current - entry) * shares
    giveback = (peak - current) * shares
    fraction = giveback / peak_profit if peak_profit > 0 else 0.0
    reasons = []
    level = "HOLD_REVIEW"
    if peak_profit > 0 and fraction >= giveback_warning_fraction:
        level = "PROTECT_PROFIT_REVIEW"
        reasons.append("PEAK_PROFIT_GIVEBACK")
    if peak_profit > 0 and fraction >= giveback_urgent_fraction:
        level = "URGENT_EXIT_REVIEW"
        reasons.append("MATERIAL_PEAK_PROFIT_GIVEBACK")
    if confirmed_trend_break:
        level = "URGENT_EXIT_REVIEW"
        reasons.append("CONFIRMED_TREND_BREAK")
    if rapid_crash:
        level = "URGENT_EXIT_REVIEW"
        reasons.append("RAPID_CRASH")
    if not fresh_data:
        reasons.append("STALE_OR_UNVERIFIED_MARKET_DATA")
    if not broker_verified:
        reasons.append("BROKER_EXECUTION_NOT_VERIFIED")
    return {"level": level, "reasons": reasons,
            "current_unrealized_gross_eur": round(current_profit, 2),
            "peak_unrealized_gross_eur": round(peak_profit, 2),
            "given_back_gross_eur": round(giveback, 2),
            "peak_profit_giveback_fraction": round(fraction, 4),
            "reference_stop": reference_stop,
            "ready_for_broker_action": bool(fresh_data and broker_verified),
            "automatic_order": False}


def pretrade_gate(*, technical_setup_verified, broker_quote_verified,
                  event_risk_reviewed, fx_verified, spread_acceptable,
                  stop_order_supported, existing_positions,
                  proposed_risk_eur, proposed_sector,
                  max_total_risk_eur=300.0, max_sector_risk_eur=150.0):
    """Independent checks; discovery alerts must not be suppressed by this gate."""
    checks = {
        "TECHNICAL_SETUP_UNVERIFIED": technical_setup_verified,
        "BROKER_QUOTE_UNVERIFIED": broker_quote_verified,
        "EVENT_RISK_UNREVIEWED": event_risk_reviewed,
        "FX_UNVERIFIED": fx_verified,
        "SPREAD_UNACCEPTABLE": spread_acceptable,
        "STOP_ORDER_SUPPORT_UNVERIFIED": stop_order_supported,
    }
    blockers = [name for name, ok in checks.items() if ok is not True]
    risk = _number(proposed_risk_eur, "proposed_risk_eur")
    if risk <= 0:
        raise ValueError("proposed_risk_eur must be positive")
    portfolio = portfolio_risk(
        list(existing_positions) + [{"planned_risk_eur": risk, "sector": proposed_sector}],
        max_total_eur=max_total_risk_eur, max_sector_eur=max_sector_risk_eur)
    blockers.extend(portfolio["blockers"])
    return {"execution_ready": not blockers, "blockers": blockers,
            "portfolio": portfolio, "discovery_alert_allowed": True,
            "automatic_order": False}
