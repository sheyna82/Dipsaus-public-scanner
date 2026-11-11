"""Fail-closed preflight before matched historical portfolio comparison.

This wrapper never downloads prices or verifies executions. It only permits
research comparison after every preregistered symbol has aligned history.
"""
from research_swing_historical_panel_coverage import audit_historical_panel
from research_swing_portfolio_benchmark import compare_portfolio_rankings

def compare_with_historical_coverage(universe, benchmarks, histories, candidates,
                                     capital, *, min_sessions=252, **kwargs):
    coverage = audit_historical_panel(universe, benchmarks, histories,
                                      min_sessions=min_sessions)
    if not coverage["aligned_length_sufficient"]:
        return {"research_only": True, "trade_ready": False, "comparison_blocked": True,
                "reason": "incomplete_or_unaligned_history", "coverage": coverage,
                "comparison": None}
    if not isinstance(candidates, (list, tuple)) or not candidates:
        raise ValueError("missing_candidates")
    expected = set(universe)
    actual = [row.get("ticker") for row in candidates if isinstance(row, dict)]
    if set(actual) != expected or len(actual) != len(expected):
        raise ValueError("candidate_universe_mismatch")
    comparison = compare_portfolio_rankings(candidates, capital, **kwargs)
    return {"research_only": True, "trade_ready": False, "comparison_blocked": False,
            "coverage": coverage, "comparison": comparison,
            "historical_profitability_established": False,
            "source_provenance_verified": False}
