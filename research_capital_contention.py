"""Deterministic offline capital contention simulation, no execution authority."""
from datetime import date, datetime
import math


def simulate_capacity_contention(candidates, *, starting_cash_eur, tranche_eur=3500,
                                 max_positions=6, initial_open_positions=0):
    """Process candidates in registered order, never by future outcome.

    Each candidate has id, entry_date, exit_date (ISO dates); no prices or
    return predictions. Cash is reserved at entry and released on exit date.
    Same-day exits are processed before new entries; a documented convention,
    not a claim about intraday tradability.
    """
    def amount(x):
        return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)
    if not amount(starting_cash_eur) or starting_cash_eur < 0:
        raise ValueError("INVALID_STARTING_CASH")
    if not amount(tranche_eur) or tranche_eur <= 0:
        raise ValueError("INVALID_TRANCHE")
    if not isinstance(max_positions, int) or isinstance(max_positions, bool) or max_positions <= 0:
        raise ValueError("INVALID_POSITION_LIMIT")
    if not isinstance(initial_open_positions, int) or isinstance(initial_open_positions, bool) or not 0 <= initial_open_positions <= max_positions:
        raise ValueError("INVALID_INITIAL_POSITIONS")
    if not isinstance(candidates, list):
        raise ValueError("INVALID_CANDIDATES")
    parsed = []
    seen = set()
    for index, c in enumerate(candidates):
        if not isinstance(c, dict) or not isinstance(c.get("id"), str) or not c["id"] or c["id"] in seen:
            raise ValueError("INVALID_CANDIDATE_ID")
        seen.add(c["id"])
        try:
            start = date.fromisoformat(c["entry_date"])
            end = date.fromisoformat(c["exit_date"])
        except (ValueError, TypeError, KeyError):
            raise ValueError("INVALID_CANDIDATE_DATES") from None
        if end <= start:
            raise ValueError("INVALID_CANDIDATE_DATES")
        parsed.append((start, index, c["id"], end))
    parsed.sort(key=lambda x: (x[0], x[1]))
    cash = float(starting_cash_eur)
    active = []
    events = []
    for entry, _, identifier, exit_date in parsed:
        retained = []
        for expiry in active:
            if expiry <= entry:
                cash += tranche_eur
            else:
                retained.append(expiry)
        active = retained
        if len(active) + initial_open_positions >= max_positions:
            reason = "POSITION_LIMIT"
        elif cash < tranche_eur:
            reason = "INSUFFICIENT_SIMULATED_CASH"
        else:
            reason = "SIMULATED_ACCEPT"
            cash -= tranche_eur
            active.append(exit_date)
        events.append({"id": identifier, "entry_date": entry.isoformat(),
                       "exit_date": exit_date.isoformat(), "decision": reason})
    return {"status": "RESEARCH_ONLY_CAPITAL_CONTENTION",
            "events": events,
            "simulated_accept_count": sum(e["decision"] == "SIMULATED_ACCEPT" for e in events),
            "simulated_reject_count": sum(e["decision"] != "SIMULATED_ACCEPT" for e in events),
            "initial_positions_are_held_constant": initial_open_positions > 0,
            "exit_proceeds_assumed_equal_to_entry": True,
            "same_day_exit_before_entry_assumption": True,
            "candidate_order_not_outcome_ranked": True,
            "historical_edge_established": False,
            "trade_ready": False, "automatic_orders": False}
