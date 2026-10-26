"""Research-only risk-budget position sizing. Never places broker orders."""
from dataclasses import dataclass
from math import floor, isfinite

RISK_BUDGETS_EUR = {"cautious": 50.0, "standard": 75.0, "exceptional": 100.0}


@dataclass(frozen=True)
class TradePlan:
    entry: float
    stop: float
    target: float
    shares: int
    investment: float
    planned_loss: float
    potential_profit: float
    reward_risk: float
    risk_budget: float
    max_capital: float
    eligible: bool
    blockers: tuple


def build_trade_plan(entry, stop, target, *, risk_budget_eur=75.0,
                     max_capital_eur=3500.0, min_reward_risk=2.0,
                     min_gross_profit_eur=150.0, verified=False):
    """EUR-denominated long-equity research sizing, whole shares only.

    A caller must independently validate quote freshness, bid/ask, technical
    stop placement, targets, news, event risk, liquidity and portfolio exposure.
    Planned loss is not a guaranteed maximum: stop-market orders may slip or gap.
    USD/other-currency instruments require separate verified FX conversion.
    """
    vals = (entry, stop, target, risk_budget_eur, max_capital_eur,
            min_reward_risk, min_gross_profit_eur)
    if any(isinstance(v, bool) or not isinstance(v, (int, float))
           or not isfinite(v) for v in vals):
        raise ValueError("All monetary inputs and thresholds must be finite numbers")
    if not (entry > 0 and 0 <= stop < entry < target):
        raise ValueError("Require 0 <= stop < entry < target")
    if risk_budget_eur <= 0 or max_capital_eur <= 0 or min_reward_risk <= 0 or min_gross_profit_eur < 0:
        raise ValueError("Budgets and thresholds must be positive")
    risk_per_share = entry - stop
    shares = max(0, min(floor(risk_budget_eur / risk_per_share),
                        floor(max_capital_eur / entry)))
    investment = round(shares * entry, 2)
    loss = round(shares * risk_per_share, 2)
    profit = round(shares * (target - entry), 2)
    rr = (target - entry) / risk_per_share
    blockers = []
    if shares == 0:
        blockers.append("ZERO_SHARES_WITHIN_BUDGET")
    if rr < min_reward_risk:
        blockers.append("REWARD_RISK_BELOW_MINIMUM")
    if profit < min_gross_profit_eur:
        blockers.append("GROSS_PROFIT_BELOW_MINIMUM")
    if not verified:
        blockers.append("BROKER_AND_SETUP_VERIFICATION_REQUIRED")
    return TradePlan(entry, stop, target, shares, investment, loss, profit,
                     round(rr, 4), risk_budget_eur, max_capital_eur,
                     not blockers, tuple(blockers))
