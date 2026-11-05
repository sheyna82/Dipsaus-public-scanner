"""Offline cash settlement timing simulation; no brokerage settlement assumptions inferred."""
from datetime import date, timedelta
import math
from research_settlement_calendar import settlement_business_date


def simulate_settled_cash(candidates, *, starting_settled_cash_eur,
                          tranche_eur=3500, settlement_calendar_days=2,
                          max_positions=6, initial_open_positions=0,
                          round_trip_cost_rate=0.005, settlement_business_days=None,
                          settlement_holidays=()):
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
    if settlement_business_days is not None:
        if not isinstance(settlement_business_days, int) or isinstance(settlement_business_days, bool) or settlement_business_days < 0:
            raise ValueError("INVALID_BUSINESS_DAY_LAG")
        if not isinstance(settlement_holidays, (list, tuple, set, frozenset)) or any(not isinstance(d, date) or isinstance(d, __import__('datetime').datetime) for d in settlement_holidays):
            raise ValueError("INVALID_HOLIDAY_CALENDAR")
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
        symbol = c.get("symbol")
        if symbol is not None and (not isinstance(symbol, str) or not symbol.strip()):
            raise ValueError("INVALID_CANDIDATE_SYMBOL")
        parsed.append((start, index, c["id"], end, ret / 100, symbol.strip().upper() if symbol is not None else None))
    parsed.sort(key=lambda x: (x[0], x[1]))
    cash = float(starting_settled_cash_eur)
    active = []
    pending = []
    events = []
    for entry, _, identifier, end, gross_return, symbol in parsed:
        retained = []
        for closing, held_symbol in active:
            if closing <= entry:
                # The exit releases the position slot, not the unsettled proceeds.
                pass
            else:
                retained.append((closing, held_symbol))
        active = retained
        still_pending = []
        for release, amount in pending:
            if release <= entry:
                cash += amount
            else:
                still_pending.append((release, amount))
        pending = still_pending
        if symbol is not None and any(held_symbol == symbol for _, held_symbol in active):
            decision = "SYMBOL_ALREADY_HELD"
        elif initial_open_positions + len(active) >= max_positions:
            decision = "POSITION_LIMIT"
        elif cash + 1e-9 < tranche_eur:
            decision = "INSUFFICIENT_SETTLED_CASH"
        else:
            decision = "SIMULATED_ACCEPT"
            cash -= tranche_eur
            active.append((end, symbol))
            proceeds = tranche_eur * max(0, 1 + gross_return - round_trip_cost_rate)
            if settlement_business_days is None:
                release_date = end + timedelta(days=settlement_calendar_days)
            else:
                release_date = date.fromisoformat(settlement_business_date(
                    end, lag_business_days=settlement_business_days,
                    holidays=settlement_holidays)["settlement_date"])
            pending.append((release_date, proceeds))
        events.append({"id": identifier, "entry_date": entry.isoformat(),
                       "exit_date": end.isoformat(), "symbol": symbol,
                       "decision": decision,
                       "future_return_used_for_entry": False})
    rejection_reasons = {reason: sum(event["decision"] == reason for event in events)
                         for reason in ("SYMBOL_ALREADY_HELD", "POSITION_LIMIT",
                                        "INSUFFICIENT_SETTLED_CASH")}
    return {
        "status": "RESEARCH_ONLY_SETTLED_CASH_SIMULATION",
        "events": events,
        "accepted_count": sum(e["decision"] == "SIMULATED_ACCEPT" for e in events),
        "rejected_count": sum(rejection_reasons.values()),
        "rejection_reasons": rejection_reasons,
        "rejection_reason_priority": ["SYMBOL_ALREADY_HELD", "POSITION_LIMIT",
                                      "INSUFFICIENT_SETTLED_CASH"],
        "cash_after_last_entry_eur": round(cash, 2),
        "unsettled_proceeds_eur": round(sum(amount for _, amount in pending), 2),
        "settlement_calendar_days_assumption": settlement_calendar_days,
        "business_day_settlement_modeled": settlement_business_days is not None,
        "settlement_business_days_assumption": settlement_business_days,
        "holiday_calendar_coverage_verified": False,
        "actual_broker_cash_verified": False,
        "prospective_validation": False,
        "trade_ready": False,
        "automatic_orders": False,
    }
