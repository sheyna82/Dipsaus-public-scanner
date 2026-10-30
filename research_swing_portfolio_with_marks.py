"""Bridge precomputed, auditable trade fills and close marks to equity research.

No price acquisition or automatic execution. The caller must supply dated,
point-in-time-consistent fills and independently verified close valuations.
"""
from research_swing_chronological_ledger import simulate_chronological_portfolio, _money
from research_swing_daily_equity import daily_equity_from_ledger


def backtest_portfolio_with_marks(trades, daily_marks, trading_dates, *,
                                  initial_capital=21000, tranche=3500,
                                  max_positions=6):
    ledger_result = simulate_chronological_portfolio(
        trades, initial_capital=initial_capital, tranche=tranche,
        max_positions=max_positions)
    equity_result = daily_equity_from_ledger(
        ledger_result["ledger"], daily_marks, trading_dates,
        initial_capital=initial_capital, tranche=tranche)
    ending_equity = _money(equity_result["ending_equity"])
    ending_cash = _money(ledger_result["ending_cash"])
    starting_cash = _money(ledger_result["initial_capital"])
    realized_pnl = _money(ledger_result["realized_net_pnl"])
    if ending_equity != ending_cash:
        raise ValueError("ending_equity_mismatch")
    if ending_cash - starting_cash != realized_pnl:
        raise ValueError("realized_pnl_reconciliation_mismatch")
    return {
        "research_only": True,
        "trade_ready": False,
        "historical_edge_proven": False,
        "cash_equity_reconciliation": {
            "passed": True,
            "ending_cash": str(ending_cash),
            "ending_equity": str(ending_equity),
            "realized_pnl": str(realized_pnl),
            "equity_minus_cash": str(ending_equity - ending_cash),
        },
        "cash_accounting": ledger_result,
        "equity": equity_result,
    }
