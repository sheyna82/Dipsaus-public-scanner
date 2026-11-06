"""Offline portfolio capital-day comparison; research only, no price forecasts."""
from decimal import Decimal, InvalidOperation

def _number(value, field):
    try:
        number = Decimal(str(value))
    except (InvalidOperation, ValueError):
        raise ValueError("INVALID_NUMBER:" + field)
    if not number.is_finite():
        raise ValueError("NONFINITE_NUMBER:" + field)
    return number

def compare(trades, capital_eur=50000, max_positions=6):
    capital = _number(capital_eur, "capital_eur")
    if capital <= 0 or not isinstance(max_positions, int) or max_positions < 1:
        raise ValueError("INVALID_PORTFOLIO_LIMITS")
    seen = set()
    rows = []
    for trade in trades:
        key = trade["id"]
        if key in seen:
            raise ValueError("DUPLICATE_TRADE_ID:" + str(key))
        seen.add(key)
        if trade.get("research_only") is not True or trade.get("trade_ready") is not False:
            raise ValueError("TRADE_NOT_RESEARCH_ONLY:" + str(key))
        allocation = _number(trade["allocation_eur"], "allocation_eur")
        days = trade["holding_sessions"]
        gross = _number(trade["gross_pnl_eur"], "gross_pnl_eur")
        costs = _number(trade["total_costs_eur"], "total_costs_eur")
        if allocation <= 0 or allocation > capital or not isinstance(days, int) or isinstance(days, bool) or days < 1 or costs < 0:
            raise ValueError("INVALID_TRADE_INPUT:" + str(key))
        net = gross - costs
        capital_days = allocation * days
        rows.append({"id": key, "net_pnl_eur": str(net),
                     "capital_days_eur_sessions": str(capital_days),
                     "net_pnl_per_1000_eur_session": str(net * 1000 / capital_days),
                     "trade_ready": False})
    # These are isolated trade observations, NOT a simultaneous portfolio simulation.
    # Dates and overlap are required before testing max_positions or total cash usage.
    return {"status": "RESEARCH_ONLY_ISOLATED_CAPITAL_DAY_COMPARISON",
            "trade_ready": False, "portfolio_validated": False,
            "simultaneous_positions_verified": False,
            "capital_eur": str(capital), "max_positions": max_positions,
            "rows": rows}
