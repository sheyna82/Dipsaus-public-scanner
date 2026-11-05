"""Research-only calendar-year momentum diagnostics, no model fitting.

Calendar years are descriptive cohorts, not independent out-of-sample tests.
"""
from collections import defaultdict
from decimal import Decimal
from research_past_return_signal_baseline import evaluate_past_return_signal


def calendar_year_momentum(stock_rows, spy_rows, *, lookback=3, horizon=3):
    observations = evaluate_past_return_signal(
        stock_rows, spy_rows, lookback=lookback, horizon=horizon)["observations"]
    # Select disjoint forward windows globally before grouping by signal year.
    # A forward window crossing December 31 belongs to its signal year.
    chosen = observations[::horizon]
    groups = defaultdict(list)
    for row in chosen:
        groups[row["signal_session"][:4]].append(row)

    def mean(rows):
        if not rows:
            return None
        return str(sum((Decimal(r["future_excess_percentage_points"]) for r in rows),
                       Decimal(0)) / len(rows))

    years = []
    for year in sorted(groups):
        rows = groups[year]
        pos = [r for r in rows if r["signal_positive_past_excess"]]
        neg = [r for r in rows if not r["signal_positive_past_excess"]]
        a, b = mean(pos), mean(neg)
        years.append({"year": year, "observations": len(rows),
                      "positive_count": len(pos), "negative_count": len(neg),
                      "positive_mean_excess_pp": a, "negative_mean_excess_pp": b,
                      "positive_minus_negative_pp":
                          str(Decimal(a) - Decimal(b)) if a is not None and b is not None else None})
    return {"method": "nonoverlapping_calendar_year_diagnostic",
            "lookback": lookback, "horizon": horizon, "years": years,
            "calendar_years_not_independent_validation": True,
            "research_only": True, "independently_verified": False,
            "predictive_skill_established": False, "trade_ready": False}
