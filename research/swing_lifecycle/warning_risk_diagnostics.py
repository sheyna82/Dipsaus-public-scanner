"""Offline diagnostics for warning exits on real, chronological OHLC bars.

Calendar-entry studies are diagnostic, not proof of trading performance.
All comparisons use the original baseline horizon; no orders are placed.
"""
from collections import defaultdict
from datetime import date
from math import isfinite
from statistics import mean

from research.swing_lifecycle.warning_exit_candidate import warning_exit_candidate


def diagnose_case(bars, *, ticker, entry_index, baseline_exit_index,
                  confirmation_sessions=1):
    """Compare a warning exit with fixed holding, including intratrade extremes.

    Entry/exit prices use opens. Exposure lows/highs include the exit session
    open, but exclude its later intraday range. This prevents using price
    movement after the simulated opening fill.
    """
    result = warning_exit_candidate(
        bars, ticker=ticker, entry_index=entry_index,
        baseline_exit_index=baseline_exit_index,
        confirmation_sessions=confirmation_sessions)
    exit_date = result["candidate_exit_date"]
    dates = [date.fromisoformat(b["date"]) for b in bars]
    exit_index = dates.index(date.fromisoformat(exit_date))
    entry = bars[entry_index]["open"]
    baseline = bars[baseline_exit_index]["open"]
    candidate = bars[exit_index]["open"]
    if any(not isinstance(v, (int, float)) or isinstance(v, bool)
           or not isfinite(v) or v <= 0 for v in (entry, baseline, candidate)):
        raise ValueError("invalid_execution_open")
    def excursion(end):
        # Entry and exit occur at their opens: neither day's intraday
        # extremes can be attributed to the position.
        prices_low = [entry] + [b["low"] for b in bars[entry_index + 1:end]] + [bars[end]["open"]]
        prices_high = [entry] + [b["high"] for b in bars[entry_index + 1:end]] + [bars[end]["open"]]
        if any(not isinstance(v, (int, float)) or isinstance(v, bool)
               or not isfinite(v) or v <= 0 for v in prices_low + prices_high):
            raise ValueError("invalid_excursion_price")
        return (min(prices_low) / entry - 1) * 100, (max(prices_high) / entry - 1) * 100
    cand_mae, cand_mfe = excursion(exit_index)
    base_mae, base_mfe = excursion(baseline_exit_index)
    early = exit_index < baseline_exit_index
    future = bars[exit_index + 1:baseline_exit_index]
    # Post-exit open through baseline open; do not attribute exit-day
    # intraday extremes to an already closed position.
    post_lows = [b["low"] for b in future] + [baseline]
    post_highs = [b["high"] for b in future] + [baseline]
    return {
        "ticker": ticker,
        "entry_date": bars[entry_index]["date"],
        "entry_quarter": f"{dates[entry_index].year}-Q{(dates[entry_index].month - 1)//3 + 1}",
        "confirmation_sessions": confirmation_sessions,
        "early_exit": early,
        "exit_date": exit_date,
        "baseline_return_pct": (baseline / entry - 1) * 100,
        "candidate_return_pct": (candidate / entry - 1) * 100,
        "return_difference_pp": (candidate - baseline) / entry * 100,
        "candidate_mae_pct": cand_mae,
        "candidate_mfe_pct": cand_mfe,
        "baseline_mae_pct": base_mae,
        "baseline_mfe_pct": base_mfe,
        "avoided_decline_5pct": early and min(post_lows) <= candidate * 0.95,
        "missed_rebound_5pct": early and max(post_highs) >= candidate * 1.05,
        "favorable_early_exit": early and candidate > baseline,
        "unfavorable_early_exit": early and candidate < baseline,
        "research_only": True,
    }


def summarize(rows):
    """Equal-weight candidate diagnostics, not portfolio P&L."""
    groups = defaultdict(list)
    for row in rows:
        for key in (("all", row["confirmation_sessions"]),
                    ("ticker", row["ticker"], row["confirmation_sessions"]),
                    ("quarter", row["entry_quarter"], row["confirmation_sessions"])):
            groups[key].append(row)
    output = []
    for key, subset in sorted(groups.items(), key=lambda item: str(item[0])):
        early = [r for r in subset if r["early_exit"]]
        output.append({
            "group": list(key),
            "candidates": len(subset),
            "early_exits": len(early),
            "mean_candidate_mae_pct": mean(r["candidate_mae_pct"] for r in subset),
            "mean_baseline_mae_pct": mean(r["baseline_mae_pct"] for r in subset),
            "mean_candidate_mfe_pct": mean(r["candidate_mfe_pct"] for r in subset),
            "sum_return_difference_pp": sum(r["return_difference_pp"] for r in subset),
            "favorable_early_exits": sum(r["favorable_early_exit"] for r in early),
            "unfavorable_early_exits": sum(r["unfavorable_early_exit"] for r in early),
            "avoided_decline_5pct": sum(r["avoided_decline_5pct"] for r in early),
            "missed_rebound_5pct": sum(r["missed_rebound_5pct"] for r in early),
        })
    return output
