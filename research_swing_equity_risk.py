"""Research-only chronological equity and drawdown summary.

Input must be a chronological *non-overlapping* portfolio equity series,
including initial capital and cash effects. End-of-period observations cannot
measure intraday drawdown or true maximum adverse excursion. No live orders.
"""
from decimal import Decimal, InvalidOperation


def _money(value):
    if isinstance(value, bool):
        raise ValueError("invalid_equity")
    try:
        n = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        raise ValueError("invalid_equity") from None
    if not n.is_finite() or n < 0:
        raise ValueError("invalid_equity")
    return n


def summarize_equity_curve(observations):
    if not isinstance(observations, (list, tuple)) or len(observations) < 2:
        raise ValueError("insufficient_equity_observations")
    from datetime import date
    seen = set()
    rows = []
    for item in observations:
        if not isinstance(item, dict):
            raise ValueError("invalid_observation")
        try:
            day = date.fromisoformat(item["date"])
        except (KeyError, TypeError, ValueError):
            raise ValueError("invalid_equity_date") from None
        if day in seen:
            raise ValueError("duplicate_equity_date")
        seen.add(day)
        rows.append((day, _money(item["equity"])))
    if rows != sorted(rows):
        raise ValueError("equity_not_chronological")
    if rows[0][1] <= 0:
        raise ValueError("invalid_initial_capital")
    peak = rows[0][1]
    max_dd = Decimal(0)
    longest_underwater = 0
    underwater = 0
    negative_streak = 0
    longest_negative_streak = 0
    negative_periods = 0
    for i, (_, equity) in enumerate(rows):
        if equity > peak:
            peak = equity
        drawdown = (peak - equity) / peak * 100
        max_dd = max(max_dd, drawdown)
        if equity < peak:
            underwater += 1
            longest_underwater = max(longest_underwater, underwater)
        else:
            underwater = 0
        if i:
            if equity < rows[i - 1][1]:
                negative_streak += 1
                negative_periods += 1
                longest_negative_streak = max(longest_negative_streak,
                                              negative_streak)
            else:
                negative_streak = 0
    start, end = rows[0][1], rows[-1][1]
    return {
        "research_only": True, "trade_ready": False,
        "risk_estimate_type": "sampled_portfolio_equity_only",
        "intraday_risk_captured": False,
        "independent_source_verification": False,
        "observations": len(rows),
        "start_equity": str(start), "end_equity": str(end),
        "net_pnl": str((end - start).quantize(Decimal("0.01"))),
        "return_pct": str(((end - start) / start * 100).quantize(Decimal("0.0001"))),
        "max_observed_drawdown_pct": str(max_dd.quantize(Decimal("0.0001"))),
        "longest_underwater_observations": longest_underwater,
        "negative_period_count": negative_periods,
        "longest_negative_streak": longest_negative_streak,
    }
