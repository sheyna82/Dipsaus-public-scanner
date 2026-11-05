"""Compare two pre-entry rankings using identical executable research assumptions.

Research-only same-session portfolios: same candidate universe, initial cash,
tranches, fill assumptions and completed future closes. No overlapping-date
capital recycling; no independent source attestation.
"""
from decimal import Decimal
from research_swing_portfolio import allocate_and_simulate
from research_swing_next_open_execution import simulate_next_open_exit


def compare_portfolio_rankings(candidates, capital, *, baseline_key="baseline_score",
                               max_positions=6, tranche=3500, horizon=5,
                               spread_bps=0, slippage_bps=0, commission_bps=0,
                               execution_model="close_optimistic_legacy"):
    if not isinstance(candidates, (list, tuple)) or not candidates:
        raise ValueError("empty_comparison")
    if baseline_key not in ("baseline_score", "relative_strength_score"):
        raise ValueError("invalid_baseline")
    if execution_model not in ("close_optimistic_legacy", "next_session_open"):
        raise ValueError("invalid_execution_model")
    hypothesis = []
    baseline = []
    for item in candidates:
        if not isinstance(item, dict):
            raise ValueError("invalid_candidate")
        if item.get("eligible") is not True:
            continue
        shared = {key: item[key] for key in ("ticker", "entry_price", "daily_closes")}
        if execution_model == "next_session_open":
            shared["next_opens"] = item["next_opens"]
        hypothesis.append({**shared, "score": item["hypothesis_score"]})
        baseline.append({**shared, "score": item[baseline_key]})
    if not hypothesis:
        raise ValueError("no_eligible_candidates")
    options = dict(max_positions=max_positions, tranche=tranche,
                   horizon=horizon, spread_bps=spread_bps,
                   slippage_bps=slippage_bps, commission_bps=commission_bps)
    if execution_model == "next_session_open":
        h = _allocate_next_open(hypothesis, capital, **options)
        b = _allocate_next_open(baseline, capital, **options)
    else:
        h = allocate_and_simulate(hypothesis, capital, **options)
        b = allocate_and_simulate(baseline, capital, **options)
    h_pnl = Decimal(h["portfolio_net_pnl"])
    b_pnl = Decimal(b["portfolio_net_pnl"])
    return {"research_only": True, "trade_ready": False,
            "comparison_type": "same_window_identical_execution_assumptions",
            "execution_model": execution_model,
            "predictive_edge_proven": False,
            "source_provenance_independently_verified": False,
            "hypothesis": h, "baseline": b,
            "net_pnl_difference": str((h_pnl - b_pnl).quantize(Decimal("0.01")))}


def _allocate_next_open(candidates, capital, *, max_positions, tranche,
                        horizon, spread_bps, slippage_bps, commission_bps):
    """Same tranche allocation as legacy model, next-open exit fills."""
    cash = Decimal(str(capital))
    ticket = Decimal(str(tranche))
    if not cash.is_finite() or not ticket.is_finite() or cash <= 0 or ticket <= 0:
        raise ValueError("invalid_allocation")
    if isinstance(max_positions, bool) or not isinstance(max_positions, int) or not 1 <= max_positions <= 6:
        raise ValueError("invalid_allocation")
    seen = set()
    ranked = []
    for item in candidates:
        ticker = item["ticker"]
        if not isinstance(ticker, str) or not ticker.strip() or ticker in seen:
            raise ValueError("invalid_or_duplicate_ticker")
        seen.add(ticker)
        score = Decimal(str(item["score"]))
        if not score.is_finite():
            raise ValueError("invalid_score")
        ranked.append((score, ticker, item))
    ranked.sort(key=lambda row: (-row[0], row[1]))
    selected = []
    remaining = cash
    for _, ticker, item in ranked:
        if len(selected) >= max_positions or remaining < ticket:
            break
        outcome = simulate_next_open_exit(
            item["entry_price"], item["daily_closes"], item["next_opens"],
            ticket, horizon=horizon, spread_bps=spread_bps,
            slippage_bps=slippage_bps, commission_bps=commission_bps)
        selected.append({"ticker": ticker, **outcome})
        remaining -= ticket
    pnl = sum((Decimal(x["net_pnl"]) for x in selected), Decimal(0))
    return {"research_only": True, "trade_ready": False,
            "selected": selected, "selected_count": len(selected),
            "initial_capital": str(cash),
            "unallocated_capital": str(remaining),
            "reserved_capital": str(cash - remaining),
            "portfolio_net_pnl": str(pnl.quantize(Decimal("0.01"))),
            "portfolio_return_pct": str((pnl / cash * 100).quantize(Decimal("0.0001")))}
