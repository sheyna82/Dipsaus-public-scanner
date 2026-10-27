"""Offline cash-only chronological portfolio ledger, no trading integration.

Input events are precomputed *executable* fills, not raw signals. The caller
must independently certify next-open timing, costs, currency and provenance.
Exit cash becomes available only after that session's entry allocation.
"""
from collections import defaultdict
from datetime import date
from decimal import Decimal, InvalidOperation


def _money(value):
    if isinstance(value, bool):
        raise ValueError("invalid_number")
    try:
        number = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        raise ValueError("invalid_number") from None
    if not number.is_finite():
        raise ValueError("invalid_number")
    return number


def simulate_chronological_portfolio(trades, *, initial_capital=21000,
                                     tranche=3500, max_positions=6):
    """Trade fields: ticker, entry_date, exit_date, net_return_pct, score.

    Returns include realized P&L only; no open-position mark-to-market.
    Exit on the same date as another entry cannot fund that entry.
    """
    capital, ticket = _money(initial_capital), _money(tranche)
    if capital <= 0 or ticket <= 0 or type(max_positions) is not int or not 1 <= max_positions <= 6:
        raise ValueError("invalid_allocation")
    if not isinstance(trades, (list, tuple)):
        raise ValueError("invalid_trades")
    entries = defaultdict(list)
    for row in trades:
        if not isinstance(row, dict):
            raise ValueError("invalid_trade")
        ticker, start, end = row["ticker"], row["entry_date"], row["exit_date"]
        if (not isinstance(ticker, str) or not ticker or type(start) is not date
                or type(end) is not date or end <= start):
            raise ValueError("invalid_trade_dates")
        ret, score = _money(row["net_return_pct"]), _money(row["score"])
        if ret < -100:
            raise ValueError("invalid_return")
        entries[start].append((score, ticker, end, ret))
    cash = capital
    positions = {}
    ledger = []
    dates = sorted(set(entries) | {item[2] for rows in entries.values() for item in rows})
    for today in dates:
        # Entries use cash known at session start, before exits settle.
        for score, ticker, end, ret in sorted(entries[today], key=lambda x: (-x[0], x[1])):
            if ticker in positions or len(positions) >= max_positions or cash < ticket:
                continue
            cash -= ticket
            positions[ticker] = (end, ret, ticket)
            ledger.append({"date": today.isoformat(), "ticker": ticker,
                           "action": "entry", "cash": str(cash)})
        for ticker in sorted(tuple(positions)):
            end, ret, invested = positions[ticker]
            if end == today:
                pnl = invested * ret / 100
                cash += invested + pnl
                del positions[ticker]
                ledger.append({"date": today.isoformat(), "ticker": ticker,
                               "action": "exit", "net_pnl": str(pnl),
                               "cash": str(cash)})
    if positions:
        raise AssertionError("unclosed_position")
    return {"research_only": True, "trade_ready": False,
            "accounting_scope": "completed_trades_only_no_daily_mtm",
            "initial_capital": str(capital), "ending_cash": str(cash),
            "realized_net_pnl": str(cash - capital),
            "realized_return_pct": str((cash / capital - 1) * 100),
            "ledger": ledger}
