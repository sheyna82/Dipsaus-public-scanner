"""Offline overlapping-position cash ledger, research-only. No order generation."""
from datetime import date
from decimal import Decimal, InvalidOperation

def _money(value):
    try:
        v = Decimal(str(value))
    except (InvalidOperation, ValueError):
        raise ValueError("INVALID_MONEY")
    if not v.is_finite() or v < 0:
        raise ValueError("INVALID_MONEY")
    return v

def simulate(trades, capital_eur=50000, max_positions=6, same_day_cash_reuse=True):
    if type(same_day_cash_reuse) is not bool:
        raise ValueError("INVALID_SAME_DAY_CASH_POLICY")
    capital = _money(capital_eur)
    if capital <= 0 or type(max_positions) is not int or max_positions < 1:
        raise ValueError("INVALID_LIMITS")
    events = []
    ids = set()
    for order_index, t in enumerate(trades):
        ident = str(t["id"])
        if ident in ids:
            raise ValueError("DUPLICATE_ID")
        ids.add(ident)
        if t.get("research_only") is not True or t.get("trade_ready") is not False:
            raise ValueError("NOT_RESEARCH_ONLY")
        try:
            start = date.fromisoformat(t["entry_date"])
            end = date.fromisoformat(t["exit_date"])
        except (ValueError, TypeError):
            raise ValueError("INVALID_DATE")
        if end <= start:
            raise ValueError("INVALID_DATE_ORDER")
        allocation = _money(t["allocation_eur"])
        if allocation <= 0:
            raise ValueError("INVALID_ALLOCATION")
        # Same-day exits release cash before entries; date-granular only.
        events.extend([(start, 1, order_index, ident, allocation), (end, 0, order_index, ident, allocation)])
    events.sort(key=lambda x: (x[0], x[1] if same_day_cash_reuse else 1 - x[1], x[2]))
    active = {}
    cash = capital
    accepted, rejected = [], []
    for day, kind, order_index, ident, allocation in events:
        if kind == 0:
            if ident in active:
                cash += active.pop(ident)
        elif allocation <= cash and len(active) < max_positions:
            cash -= allocation
            active[ident] = allocation
            accepted.append(ident)
        else:
            rejected.append({"id": ident, "reason": "INSUFFICIENT_CASH" if allocation > cash else "MAX_POSITIONS"})
    return {"status": "RESEARCH_ONLY_DATE_GRANULAR_CASH_LEDGER",
            "trade_ready": False, "portfolio_validated": False,
            "accepted_ids": accepted, "rejected": rejected,
            "ending_reserved_eur": str(sum(active.values(), Decimal(0))),
            "ending_free_cash_eur": str(cash),
            "limitations": ["same-day cash reuse policy: " + ("enabled" if same_day_cash_reuse else "disabled"), "no intraday sequence", "no PnL reinvestment", "no currency conversion",
                            "no order execution or settlement model", "not a trading recommendation"]}
