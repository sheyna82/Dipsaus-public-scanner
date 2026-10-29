"""Chronological out-of-sample reporting for warning exit research.

No strategy tuning, live trading, or claims of verified historical provenance.
The caller supplies preselected entry candidates and dated OHLC histories.
"""
from datetime import date
from decimal import Decimal
from research.swing_lifecycle.warning_portfolio_comparison import compare_warning_exit_portfolios


def evaluate_warning_exit_holdout(cases, *, cutoff, embargo_days=15,
                                  cost_bps_per_side=10,
                                  initial_capital=21000, tranche=3500,
                                  max_positions=6):
    """Keep whole trades on one side of the cutoff; purge crossing trades.

    Training trades must finish strictly before cutoff minus embargo.
    Holdout trades must enter strictly after cutoff plus embargo.
    No parameter fitting is performed; both partitions use fixed rules.
    """
    if type(cutoff) is not date or type(embargo_days) is not int or embargo_days < 0:
        raise ValueError("invalid_split")
    if not isinstance(cases, (list, tuple)):
        raise ValueError("invalid_cases")
    training, holdout = [], []
    purged = 0
    for case in cases:
        bars = case["bars"]
        start = date.fromisoformat(bars[case["entry_index"]]["date"])
        finish = date.fromisoformat(bars[case["baseline_exit_index"]]["date"])
        if finish < cutoff and (cutoff - finish).days > embargo_days:
            training.append(case)
        elif start > cutoff and (start - cutoff).days > embargo_days:
            holdout.append(case)
        else:
            purged += 1
    options = dict(cost_bps_per_side=cost_bps_per_side,
                   initial_capital=initial_capital, tranche=tranche,
                   max_positions=max_positions)
    def summarize(rows):
        if not rows:
            return {"trade_candidates": 0, "result": None}
        result = compare_warning_exit_portfolios(rows, **options)
        diagnostics = result["candidate_diagnostics"]
        return {
            "trade_candidates": len(rows),
            "warning_candidates": sum(x["warning_decision_date"] is not None
                                      for x in diagnostics),
            "sessions_released_early": sum(
                x["sessions_capital_released_early"] for x in diagnostics),
            "candidate_counterfactual_baseline_minus_exit_pct_points_sum": str(
                sum((Decimal(x["counterfactual_baseline_minus_candidate_pct_points"])
                     for x in diagnostics), Decimal(0))),
            "result": result,
        }
    return {
        "research_only": True, "trade_ready": False,
        "historical_edge_proven": False, "market_data_provenance_verified": False,
        "cutoff": cutoff.isoformat(), "embargo_days": embargo_days,
        "purged_crossing_or_near_cutoff": purged,
        "training": summarize(training), "holdout": summarize(holdout),
        "warning": "Fixed rules only. Requires independently verified market data, survivorship checks and multiple rolling cutoffs before inference.",
    }
