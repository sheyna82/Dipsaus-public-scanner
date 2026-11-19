"""Isolated EUR research portfolio ledger. No broker integration or orders.

Events are date-granular. An accepted position releases its reserved principal
plus *realized* net PnL at exit. Same-day cash reuse is disabled by default.
No price discovery, settlement guarantee, or claim of historical profitability.
"""
from datetime import date
from decimal import Decimal, InvalidOperation

def money(value, *, nonnegative=True):
    if isinstance(value, bool):
        raise ValueError("INVALID_MONEY")
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        raise ValueError("INVALID_MONEY")
    if not result.is_finite() or (nonnegative and result < 0):
        raise ValueError("INVALID_MONEY")
    return result

def simulate_research(trades, *, starting_cash_eur="50000", max_positions=6,
                      same_day_cash_reuse=False):
    if not isinstance(trades, list) or type(max_positions) is not int or max_positions < 1:
        raise ValueError("INVALID_PORTFOLIO_INPUT")
    if type(same_day_cash_reuse) is not bool:
        raise ValueError("INVALID_CASH_POLICY")
    cash = money(starting_cash_eur)
    if cash <= 0:
        raise ValueError("INVALID_STARTING_CASH")
    events, seen = [], set()
    for index, row in enumerate(trades):
        if not isinstance(row, dict) or row.get("research_only") is not True or row.get("trade_ready") is not False:
            raise ValueError("NOT_RESEARCH_ONLY")
        ident = row.get("id")
        if not isinstance(ident, str) or not ident or ident in seen:
            raise ValueError("INVALID_OR_DUPLICATE_ID")
        seen.add(ident)
        try:
            start, end = date.fromisoformat(row["entry_date"]), date.fromisoformat(row["exit_date"])
        except (KeyError, ValueError, TypeError) as exc:
            raise ValueError("INVALID_DATES") from exc
        if end <= start:
            raise ValueError("INVALID_DATE_ORDER")
        principal = money(row.get("allocation_eur"))
        pnl = money(row.get("realized_net_pnl_eur"), nonnegative=False)
        if principal <= 0 or principal + pnl < 0:
            raise ValueError("INVALID_POSITION_VALUE")
        events.extend([(start, 1, index, ident, principal, pnl),
                       (end, 0, index, ident, principal, pnl)])
    # On the same date, conservative policy processes new entries before exits.
    events.sort(key=lambda e: (e[0], e[1] if same_day_cash_reuse else 1-e[1], e[2]))
    active, accepted, rejected, realized = {}, [], [], Decimal(0)
    for day, kind, _, ident, principal, pnl in events:
        if kind == 0:
            if ident in active:
                reserved, realized_pnl = active.pop(ident)
                cash += reserved + realized_pnl
                realized += realized_pnl
        elif principal <= cash and len(active) < max_positions:
            cash -= principal
            active[ident] = (principal, pnl)
            accepted.append(ident)
        else:
            rejected.append({"id": ident, "reason": "INSUFFICIENT_CASH" if principal > cash else "MAX_POSITIONS"})
    reserved = sum((x[0] for x in active.values()), Decimal(0))
    return {"schema": "dipsaus_isolated_portfolio_research_v1", "research_only": True,
            "trade_ready": False, "broker_connected": False, "orders_generated": False,
            "starting_cash_eur": str(money(starting_cash_eur)),
            "ending_cash_eur": str(cash), "ending_reserved_eur": str(reserved),
            "realized_net_pnl_eur": str(realized), "accepted_ids": accepted,
            "rejected": rejected, "max_positions": max_positions,
            "same_day_cash_reuse": same_day_cash_reuse,
            "limitations": ["historical realized PnL is an outcome input, not a ranking feature",
                            "no execution, settlement, FX, spreads, or mark-to-market",
                            "rejected trades do not realize hypothetical PnL"]}
