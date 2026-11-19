"""Research-only opportunity-cost attribution for rejected, timestamped trades."""
from decimal import Decimal, InvalidOperation
from integrated_overlapping_capital_ledger import simulate

def _decimal(value):
    try:
        x = Decimal(str(value))
    except (InvalidOperation, ValueError):
        raise ValueError("INVALID_OUTCOME")
    if not x.is_finite():
        raise ValueError("NONFINITE_OUTCOME")
    return x

def attribute(trades, realized_outcomes=None, capital_eur=50000, max_positions=6):
    ledger = simulate(trades, capital_eur=capital_eur, max_positions=max_positions)
    realized_outcomes = realized_outcomes or {}
    accepted = set(ledger["accepted_ids"])
    rejected = {row["id"]: row["reason"] for row in ledger["rejected"]}
    ids = accepted | set(rejected)
    if set(realized_outcomes) - ids:
        raise ValueError("UNKNOWN_OUTCOME_ID")
    rows = []
    for t in trades:
        ident = str(t["id"])
        if ident not in rejected:
            continue
        outcome = realized_outcomes.get(ident)
        if outcome is None:
            rows.append({"id": ident, "reason": rejected[ident], "outcome_known": False,
                         "foregone_net_pnl_eur": None})
        else:
            if outcome.get("observed_after_exit") is not True or outcome.get("source_verified") is not True:
                raise ValueError("UNVERIFIED_FUTURE_OUTCOME:" + ident)
            gross = _decimal(outcome["gross_pnl_eur"])
            costs = _decimal(outcome["total_costs_eur"])
            if costs < 0:
                raise ValueError("INVALID_OUTCOME_COSTS")
            rows.append({"id": ident, "reason": rejected[ident], "outcome_known": True,
                         "foregone_net_pnl_eur": str(gross - costs)})
    return {"status": "RESEARCH_ONLY_REJECTED_OPPORTUNITY_ATTRIBUTION",
            "trade_ready": False, "causal_opportunity_cost_proven": False,
            "accepted_count": len(accepted), "rejected_count": len(rejected),
            "rejected_outcomes": rows,
            "limitations": ["counterfactual returns do not establish executable fills",
                            "same-day ordering is date-granular",
                            "no claim of causal strategy superiority"]}
