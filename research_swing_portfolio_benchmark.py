"""Compare two pre-entry rankings using identical executable research assumptions.

Research-only same-session portfolios: same candidate universe, initial cash,
tranches, fill assumptions and completed future closes. No overlapping-date
capital recycling; no independent source attestation.
"""
from decimal import Decimal
from research_swing_portfolio import allocate_and_simulate


def compare_portfolio_rankings(candidates, capital, *, baseline_key="baseline_score",
                               max_positions=6, tranche=3500, horizon=5,
                               spread_bps=0, slippage_bps=0, commission_bps=0):
    if not isinstance(candidates, (list, tuple)) or not candidates:
        raise ValueError("empty_comparison")
    if baseline_key not in ("baseline_score", "relative_strength_score"):
        raise ValueError("invalid_baseline")
    hypothesis = []
    baseline = []
    for item in candidates:
        if not isinstance(item, dict):
            raise ValueError("invalid_candidate")
        if item.get("eligible") is not True:
            continue
        shared = {key: item[key] for key in ("ticker", "entry_price", "daily_closes")}
        hypothesis.append({**shared, "score": item["hypothesis_score"]})
        baseline.append({**shared, "score": item[baseline_key]})
    if not hypothesis:
        raise ValueError("no_eligible_candidates")
    options = dict(max_positions=max_positions, tranche=tranche,
                   horizon=horizon, spread_bps=spread_bps,
                   slippage_bps=slippage_bps, commission_bps=commission_bps)
    h = allocate_and_simulate(hypothesis, capital, **options)
    b = allocate_and_simulate(baseline, capital, **options)
    h_pnl = Decimal(h["portfolio_net_pnl"])
    b_pnl = Decimal(b["portfolio_net_pnl"])
    return {"research_only": True, "trade_ready": False,
            "comparison_type": "same_window_identical_execution_assumptions",
            "predictive_edge_proven": False,
            "source_provenance_independently_verified": False,
            "hypothesis": h, "baseline": b,
            "net_pnl_difference": str((h_pnl - b_pnl).quantize(Decimal("0.01")))}
