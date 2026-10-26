"""Research-only profit/risk guardrails for predeclared swing strategies.

Avoid optimizing a single sample: this function reports pass/fail of fixed
risk constraints, never selects a winning policy. Metrics require real dated
equity observations and must be evaluated on held-out data separately.
"""
from decimal import Decimal, InvalidOperation
from research_swing_equity_risk import summarize_equity_curve


def _decimal(value):
    if isinstance(value, bool):
        raise ValueError("invalid_risk_threshold")
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        raise ValueError("invalid_risk_threshold") from None
    if not result.is_finite():
        raise ValueError("invalid_risk_threshold")
    return result


def assess_profit_risk(strategies, *, max_drawdown_pct=15,
                       max_negative_streak=5, min_observations=20):
    """Evaluate each predeclared strategy against identical fixed guardrails."""
    if not isinstance(strategies, dict) or not strategies:
        raise ValueError("empty_strategies")
    dd_limit = _decimal(max_drawdown_pct)
    if not 0 <= dd_limit <= 100:
        raise ValueError("invalid_risk_threshold")
    if (isinstance(max_negative_streak, bool) or
            not isinstance(max_negative_streak, int) or
            max_negative_streak < 0 or
            isinstance(min_observations, bool) or
            not isinstance(min_observations, int) or
            min_observations < 2):
        raise ValueError("invalid_risk_threshold")
    results = {}
    for name, observations in strategies.items():
        if not isinstance(name, str) or not name.strip():
            raise ValueError("invalid_strategy")
        summary = summarize_equity_curve(observations)
        enough = summary["observations"] >= min_observations
        drawdown_ok = _decimal(summary["max_observed_drawdown_pct"]) <= dd_limit
        streak_ok = summary["longest_negative_streak"] <= max_negative_streak
        positive = _decimal(summary["net_pnl"]) > 0
        results[name] = {
            **summary,
            "minimum_sample_met": enough,
            "drawdown_limit_met": drawdown_ok,
            "loss_streak_limit_met": streak_ok,
            "positive_net_pnl": positive,
            "research_guardrails_met":
                enough and drawdown_ok and streak_ok and positive,
        }
    return {
        "research_only": True, "trade_ready": False,
        "predictive_edge_proven": False,
        "independent_source_verification": False,
        "best_strategy_selected": False,
        "limits": {"max_drawdown_pct": str(dd_limit),
                   "max_negative_streak": max_negative_streak,
                   "min_observations": min_observations},
        "strategies": results,
    }
