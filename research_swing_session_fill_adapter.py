"""Convert session-indexed, post-signal next-open fills into research proposals.

Price series are chronological session bars. Signals are dated indices known
only after their session closes. Exit is the open after the holding window.
This is an offline adapter, not an order interface or historical data fetcher.
"""
from datetime import date
from research_swing_chronological_ledger import _money


def proposals_from_bars(series_by_ticker, signals, *, horizon=10,
                        roundtrip_cost_bps=50):
    if type(horizon) is not int or not 1 <= horizon <= 30:
        raise ValueError("invalid_horizon")
    costs = _money(roundtrip_cost_bps)
    if costs < 0 or costs >= 10000:
        raise ValueError("invalid_costs")
    proposals = []
    for signal in signals:
        ticker = signal["ticker"]
        bars = series_by_ticker[ticker]
        decision_index = signal["decision_index"]
        if type(decision_index) is not int or decision_index < 0:
            raise ValueError("invalid_decision_index")
        entry_index = decision_index + 1
        exit_index = entry_index + horizon
        if exit_index >= len(bars):
            raise ValueError("incomplete_forward_bars")
        dates = [bar["date"] for bar in bars]
        if (any(type(day) is not date for day in dates)
                or dates != sorted(set(dates))):
            raise ValueError("invalid_session_calendar")
        entry = _money(bars[entry_index]["open"])
        exit_ = _money(bars[exit_index]["open"])
        if entry <= 0 or exit_ <= 0:
            raise ValueError("invalid_open_price")
        # Round-trip cost is charged as a conservative return haircut;
        # exact per-side share sizing and commissions remain a later task.
        net_pct = (exit_ / entry - 1) * 100 - costs / 100
        if net_pct < -100:
            raise ValueError("invalid_net_return")
        proposals.append({
            "ticker": ticker, "entry_date": dates[entry_index],
            "exit_date": dates[exit_index], "net_return_pct": str(net_pct),
            "score": signal["score"],
            "decision_date": dates[decision_index],
            "cost_model": "fixed_roundtrip_bps_return_haircut",
        })
    return proposals
