"""Compare dated warning exits with baseline using the existing cash ledger.

Research only. Prices are assumed executable next-open proxies; the caller
must certify price provenance, corporate actions, FX, costs and fill realism.
"""
from datetime import date
from decimal import Decimal
from research_swing_chronological_ledger import simulate_chronological_portfolio
from research.swing_lifecycle.warning_exit_candidate import warning_exit_candidate


def compare_warning_exit_portfolios(cases, *, initial_capital=21000,
                                    tranche=3500, max_positions=6,
                                    cost_bps_per_side=10):
    if not isinstance(cases, (list, tuple)) or not cases:
        raise ValueError("empty_cases")
    if isinstance(cost_bps_per_side, bool) or not isinstance(cost_bps_per_side, (int, float)) or not 0 <= cost_bps_per_side < 10000:
        raise ValueError("invalid_cost")
    cost = Decimal(str(cost_bps_per_side)) / Decimal(10000)
    baseline, protected, diagnostics = [], [], []
    seen = set()
    for case in cases:
        ticker = case["ticker"]
        bars = case["bars"]
        entry = case["entry_index"]
        end = case["baseline_exit_index"]
        key = (ticker, bars[entry]["date"])
        if key in seen:
            raise ValueError("duplicate_trade")
        seen.add(key)
        candidate = warning_exit_candidate(
            bars, ticker=ticker, entry_index=entry, baseline_exit_index=end)
        entry_open = Decimal(str(bars[entry]["open"]))
        if not entry_open.is_finite() or entry_open <= 0:
            raise ValueError("invalid_entry_open")
        def ledger_trade(exit_index):
            exit_open = Decimal(str(bars[exit_index]["open"]))
            if not exit_open.is_finite() or exit_open <= 0:
                raise ValueError("invalid_exit_open")
            net_return = ((exit_open * (1-cost)) / (entry_open * (1+cost)) - 1) * 100
            return {"ticker": ticker,
                    "entry_date": date.fromisoformat(bars[entry]["date"]),
                    "exit_date": date.fromisoformat(bars[exit_index]["date"]),
                    "net_return_pct": str(net_return),
                    "score": case["score"]}
        protected_exit = next(i for i in range(entry+1, end+1)
                              if bars[i]["date"] == candidate["candidate_exit_date"])
        baseline.append(ledger_trade(end))
        protected.append(ledger_trade(protected_exit))
        # Counterfactual per candidate, not attribution of portfolio P&L.
        baseline_open = Decimal(str(bars[end]["open"]))
        candidate_open = Decimal(str(bars[protected_exit]["open"]))
        candidate = dict(candidate)
        candidate["counterfactual_baseline_minus_candidate_pct_points"] = str(
            (baseline_open - candidate_open) / entry_open * 100)
        candidate["sessions_capital_released_early"] = end - protected_exit
        diagnostics.append(candidate)
    original = simulate_chronological_portfolio(
        baseline, initial_capital=initial_capital, tranche=tranche,
        max_positions=max_positions)
    guarded = simulate_chronological_portfolio(
        protected, initial_capital=initial_capital, tranche=tranche,
        max_positions=max_positions)
    return {
        "research_only": True, "trade_ready": False,
        "fills_independently_verified": False,
        "price_source_verified": False, "fx_and_corporate_actions_verified": False,
        "execution_proxy": "next_session_open_symmetric_costs",
        "cost_bps_per_side": str(cost_bps_per_side),
        "baseline": original, "warning_protected": guarded,
        "difference_realized_pnl": str(
            Decimal(guarded["realized_net_pnl"]) -
            Decimal(original["realized_net_pnl"])),
        "candidate_diagnostics": diagnostics,
        "limitation": "Counterfactual is not portfolio P&L attribution; no daily mark-to-market drawdown, real limit fill or walk-forward selection.",
    }
