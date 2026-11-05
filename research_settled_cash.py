"""Offline cash settlement timing simulation; no brokerage settlement assumptions inferred."""
from datetime import date, timedelta
import math


def simulate_settled_cash(candidates, *, starting_settled_cash_eur,
                          tranche_eur=3500, settlement_calendar_days=2,
                          max_positions=6, initial_open_positions=0,
                          round_trip_cost_rate=0.005):
    """No same-day reuse: proceeds become usable on explicit settlement date.

    Calendar days are an illustrative parameter, NOT a market-specific settlement
    rule. Exit proceeds are based on realized gross returns minus cost rate;
    future outcomes never influence entry priority. Exits are released only
    on settlement date. Existing positions permanently occupy initial slots.
    """
    def finite(x):
        return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)
    if not finite(starting_settled_cash_eur) or starting_settled_cash_eur < 0:
        raise ValueError("INVALID_STARTING_CASH")
    if not finite(tranche_eur) or tranche_eur <= 0:
        raise ValueError("INVALID_TRANCHE")
    if not isinstance(settlement_calendar_days, int) or isinstance(settlement_calendar_days, bool) or settlement_calendar_days < 0:
        raise ValueError("INVALID_SETTLEMENT_DAYS")
    if not isinstance(max_positions, int) or isinstance(max_positions, bool) or max_positions < 1:
        raise ValueError("INVALID_POSITION_LIMIT")
    if not isinstance(initial_open_positions, int) or isinstance(initial_open_positions, bool) or not 0 <= initial_open_positions <= max_positions:
        raise ValueError("INVALID_INITIAL_POSITIONS")
    if not finite(round_trip_cost_rate) or not 0 <= round_trip_cost_rate < 1:
        raise ValueError("INVALID_COST_RATE")
    if not isinstance(candidates, list):
        raise ValueError("INVALID_CANDIDATES")
    parsed = []
    ids = set()
    for index, c in enumerate(candidates):
        if not isinstance(c, dict) or not isinstance(c.get("id"), str) or not c["id"] or c["id"] in ids:
            raise ValueError("INVALID_CANDIDATE_ID")
        ids.add(c["id"])
        try:
            start, end = date.fromisoformat(c["entry_date"]), date.fromisoformat(c["exit_date"])
        except (ValueError, TypeError, KeyError):
            raise ValueError("INVALID_CANDIDATE_DATES") from None
        ret = c.get("realized_return_pct")
        if end <= start or not finite(ret) or ret < -100:
            raise ValueError("INVALID_CANDIDATE_OUTCOME")
        parsed.append((start, index, c["id"], end, ret / 100))
    parsed.sort(key=lambda x: (x[0], x[1]))
    cash = float(starting_settled_cash_eur)
    active = []
    pending = []
    events = []
    for entry, _, identifier, end, gross_return in parsed:
        retained = []
        for closing in active:
            if closing <= entry:
                # The exit releases the position slot, not the unsettled proceeds.
                pass
            else:
                retained.append(closing)
        active = retained
        still_pending = []
        for release, amount in pending:
            if release <= entry:
                cash += amount
            else:
                still_pending.append((release, amount))
        pending = still_pending
        if initial_open_positions + len(active) >= max_positions:
            decision = "POSITION_LIMIT"
        elif cash + 1e-9 < tranche_eur:
            decision = "INSUFFICIENT_SETTLED_CASH"
        else:
            decision = "SIMULATED_ACCEPT"
            cash -= tranche_eur
            active.append(end)
            proceeds = tranche_eur * max(0, 1 + gross_return - round_trip_cost_rate)
            pending.append((end + timedelta(days=settlement_calendar_days), proceeds))
        events.append({"id": identifier, "entry_date": entry.isoformat(),
                       "exit_date": end.isoformat(), "decision": decision,
                       "future_return_used_for_entry": False})
    return {
        "status": "RESEARCH_ONLY_SETTLED_CASH_SIMULATION",
        "events": events,
        "accepted_count": sum(e["decision"] == "SIMULATED_ACCEPT" for e in events),
        "cash_after_last_entry_eur": round(cash, 2),
        "unsettled_proceeds_eur": round(sum(amount for _, amount in pending), 2),
        "settlement_calendar_days_assumption": settlement_calendar_days,
        "business_day_settlement_modeled": False,
        "actual_broker_cash_verified": False,
        "prospective_validation": False,
        "trade_ready": False,
        "automatic_orders": False,
    }
