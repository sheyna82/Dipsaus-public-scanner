"""Offline event-time capital accounting for candidate overlap; never places orders."""
from datetime import date
import math


def simulate_realized_cashflows(candidates, *, starting_cash_eur, tranche_eur=3500,
                                max_positions=6, initial_open_positions=0,
                                round_trip_cost_rate=0.005):
    """Entry decisions use only currently released cash and occupied slots.

    Candidate fields: id, entry_date, exit_date, realized_return_pct.
    Realized return is used ONLY when an accepted trade exits; never for entry
    ranking. Same-day exits are assumed settled before entries (optimistic).
    Existing initial positions occupy slots throughout the entire simulation.
    Cash proceeds may be below or above principal; no margin/borrowed cash.
    """
    def valid_number(x):
        return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)
    if not valid_number(starting_cash_eur) or starting_cash_eur < 0:
        raise ValueError("INVALID_STARTING_CASH")
    if not valid_number(tranche_eur) or tranche_eur <= 0:
        raise ValueError("INVALID_TRANCHE")
    if not isinstance(max_positions, int) or isinstance(max_positions, bool) or max_positions < 1:
        raise ValueError("INVALID_POSITION_LIMIT")
    if not isinstance(initial_open_positions, int) or isinstance(initial_open_positions, bool) or not 0 <= initial_open_positions <= max_positions:
        raise ValueError("INVALID_INITIAL_POSITIONS")
    if not valid_number(round_trip_cost_rate) or not 0 <= round_trip_cost_rate < 1:
        raise ValueError("INVALID_COST_RATE")
    if not isinstance(candidates, list):
        raise ValueError("INVALID_CANDIDATES")
    parsed = []
    seen = set()
    for i, item in enumerate(candidates):
        if not isinstance(item, dict) or not isinstance(item.get("id"), str) or not item["id"] or item["id"] in seen:
            raise ValueError("INVALID_CANDIDATE_ID")
        seen.add(item["id"])
        try:
            entry = date.fromisoformat(item["entry_date"])
            exit_day = date.fromisoformat(item["exit_date"])
        except (ValueError, TypeError, KeyError):
            raise ValueError("INVALID_CANDIDATE_DATES") from None
        ret = item.get("realized_return_pct")
        if exit_day <= entry or not valid_number(ret) or ret < -100:
            raise ValueError("INVALID_CANDIDATE_OUTCOME")
        parsed.append((entry, i, item["id"], exit_day, ret / 100))
    parsed.sort(key=lambda x: (x[0], x[1]))
    cash = float(starting_cash_eur)
    open_trades = []
    events = []
    realized_pnl = 0.0
    for entry, _, identifier, exit_day, gross_return in parsed:
        still_open = []
        for closing, principal, net_return in open_trades:
            if closing <= entry:
                proceeds = principal * max(0.0, 1 + net_return)
                cash += proceeds
                realized_pnl += proceeds - principal
            else:
                still_open.append((closing, principal, net_return))
        open_trades = still_open
        if initial_open_positions + len(open_trades) >= max_positions:
            decision = "POSITION_LIMIT"
        elif cash < tranche_eur:
            decision = "INSUFFICIENT_SIMULATED_CASH"
        else:
            decision = "SIMULATED_ACCEPT"
            cash -= tranche_eur
            open_trades.append((exit_day, tranche_eur, gross_return - round_trip_cost_rate))
        events.append({"id": identifier, "entry_date": entry.isoformat(),
                       "exit_date": exit_day.isoformat(), "decision": decision,
                       "outcome_used_for_entry": False})
    # Do not credit proceeds from positions whose exits have not yet occurred.
    return {
        "status": "RESEARCH_ONLY_REALIZED_CASHFLOW_SIMULATION",
        "events": events,
        "cash_after_last_entry_eur": round(cash, 2),
        "realized_pnl_from_closed_positions_eur": round(realized_pnl, 2),
        "unsettled_simulated_positions": len(open_trades),
        "accepted_count": sum(x["decision"] == "SIMULATED_ACCEPT" for x in events),
        "same_day_exit_before_entry_assumption": True,
        "initial_positions_held_constant": initial_open_positions > 0,
        "settlement_lag_modeled": False,
        "slippage_modeled": False,
        "prospective_validation": False,
        "trade_ready": False,
        "automatic_orders": False,
    }
