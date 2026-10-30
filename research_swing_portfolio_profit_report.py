"""Attach independent closed-trade diagnostics to same-window portfolio comparison.

Uses simulated net P&L from the selected trades in each arm, never gross
returns. Does not claim chronological equity drawdown or real data validity.
"""
from research_swing_closed_trade_profit_diagnostics import analyze_closed_trade_pnl
from research_swing_portfolio_benchmark import compare_portfolio_rankings


def compare_portfolio_profit_diagnostics(candidates, capital, **options):
    if options.get("execution_model", "next_session_open") != "next_session_open":
        raise ValueError("next_open_execution_required")
    comparison = compare_portfolio_rankings(
        candidates, capital, **{**options, "execution_model": "next_session_open"})
    diagnostics = {}
    for arm in ("hypothesis", "baseline"):
        selected = comparison[arm]["selected"]
        if not selected:
            raise ValueError("no_selected_trades")
        diagnostics[arm] = analyze_closed_trade_pnl([trade["net_pnl"] for trade in selected])
        if diagnostics[arm]["net_profit"] != comparison[arm]["portfolio_net_pnl"]:
            raise ValueError("portfolio_profit_reconciliation_failed")
    return {
        "research_only": True,
        "trade_ready": False,
        "execution_model": "next_session_open",
        "comparison": comparison,
        "diagnostics": diagnostics,
        "independent_real_market_validation": False,
        "chronological_portfolio_drawdown_available": False,
    }
