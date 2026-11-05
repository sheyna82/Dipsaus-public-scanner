"""Predeclared exit-policy comparison using next-session-open execution.

A completed session close triggers a decision; actual modeled exit uses the
following session open. Compare policies on identical data and costs.
No policy winner is selected using these outcomes.
"""
from decimal import Decimal
from research_swing_next_open_execution import simulate_next_open_exit


def compare_exit_policies(trades, *, horizon=5, target_pct=5,
                          trailing_pct=3, spread_bps=0,
                          slippage_bps=0, commission_bps=0):
    if not isinstance(trades, (list, tuple)) or not trades:
        raise ValueError("empty_trade_cohort")
    if isinstance(horizon, bool) or horizon not in (3, 5, 10):
        raise ValueError("invalid_horizon")
    policies = {
        "fixed_horizon": {},
        "close_target_next_open": {"target_pct": target_pct},
        "close_trailing_next_open": {"trailing_pct": trailing_pct},
    }
    results = {}
    seen = set()
    for name, policy in policies.items():
        rows = []
        for trade in trades:
            if not isinstance(trade, dict):
                raise ValueError("invalid_trade")
            ticker = trade["ticker"]
            if not isinstance(ticker, str) or not ticker.strip():
                raise ValueError("invalid_ticker")
            if ticker in seen and name == "fixed_horizon":
                raise ValueError("duplicate_ticker")
            outcome = simulate_next_open_exit(
                trade["entry_price"], trade["daily_closes"],
                trade["next_opens"], trade["capital"], horizon=horizon,
                spread_bps=spread_bps, slippage_bps=slippage_bps,
                commission_bps=commission_bps, **policy)
            rows.append({"ticker": ticker, **outcome})
            if name == "fixed_horizon":
                seen.add(ticker)
        pnl = sum((Decimal(row["net_pnl"]) for row in rows), Decimal(0))
        capital = sum((Decimal(str(row["capital"])) for row in trades), Decimal(0))
        results[name] = {
            "net_pnl": str(pnl.quantize(Decimal("0.01"))),
            "return_on_allocated_capital_pct":
                str((pnl / capital * 100).quantize(Decimal("0.0001"))),
            "negative_trade_count": sum(Decimal(row["net_pnl"]) < 0 for row in rows),
            "trades": rows}
    return {"research_only": True, "trade_ready": False,
            "predictive_edge_proven": False,
            "policies_fixed_before_outcomes": "caller_must_attest",
            "policy_selection_from_this_sample_allowed": False,
            "exit_execution": "following_session_open",
            "results": results}
