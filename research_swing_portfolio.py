"""Offline, deterministic capital allocation research.

Candidates are externally scored *before* selection. This module never predicts
prices or sends orders; it measures capacity and simulated net portfolio P&L.
"""
from decimal import Decimal, InvalidOperation
from research_swing_net_pnl import simulate_swing


def _num(v, label):
    if isinstance(v, bool):
        raise ValueError(label)
    try:
        x = Decimal(str(v))
    except (InvalidOperation, ValueError, TypeError):
        raise ValueError(label) from None
    if not x.is_finite():
        raise ValueError(label)
    return x


def allocate_and_simulate(candidates, capital, *, max_positions=6,
                          tranche=3500, horizon=5, spread_bps=0,
                          slippage_bps=0, commission_bps=0):
    """Rank candidates by predeclared score; allocate cash in whole tranches.

    Assumes simultaneous entry and one common evaluation window. Does not
    reallocate proceeds during that window. Duplicate tickers are rejected.
    Returns P&L on initial portfolio capital, including idle cash.
    """
    available = _num(capital, "invalid_capital")
    ticket = _num(tranche, "invalid_tranche")
    if available <= 0 or ticket <= 0 or isinstance(max_positions, bool) or not isinstance(max_positions, int) or not 1 <= max_positions <= 6:
        raise ValueError("invalid_allocation")
    if not isinstance(candidates, (list, tuple)):
        raise ValueError("invalid_candidates")
    seen = set()
    ranked = []
    for item in candidates:
        if not isinstance(item, dict):
            raise ValueError("invalid_candidate")
        ticker = item.get("ticker")
        if not isinstance(ticker, str) or not ticker.strip() or ticker in seen:
            raise ValueError("invalid_or_duplicate_ticker")
        seen.add(ticker)
        score = _num(item.get("score"), "invalid_score")
        ranked.append((score, ticker, item))
    ranked.sort(key=lambda row: (-row[0], row[1]))
    results = []
    remaining = available
    for _, ticker, item in ranked:
        if len(results) >= max_positions or remaining < ticket:
            break
        outcome = simulate_swing(
            item["entry_price"], item["daily_closes"], ticket,
            horizon=horizon, spread_bps=spread_bps,
            slippage_bps=slippage_bps, commission_bps=commission_bps,
        )
        results.append({"ticker": ticker, **outcome})
        # Reserve entire tranche: any unused part stays idle during this window.
        remaining -= ticket
    pnl = sum((Decimal(row["net_pnl"]) for row in results), Decimal(0))
    return {
        "research_only": True, "trade_ready": False,
        "selected": results, "selected_count": len(results),
        "initial_capital": str(available),
        "unallocated_capital": str(remaining),
        "reserved_capital": str(available - remaining),
        "portfolio_net_pnl": str(pnl.quantize(Decimal("0.01"))),
        "portfolio_return_pct": str((pnl / available * 100).quantize(Decimal("0.0001"))),
    }
