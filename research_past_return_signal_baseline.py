"""Causal research-only momentum baseline using past closes, never future prices as features."""
from decimal import Decimal
from research_rolling_excess_returns import rolling_excess_returns


def evaluate_past_return_signal(stock_rows, spy_rows, *, lookback=3, horizon=3):
    if type(lookback) is not int or lookback < 1 or type(horizon) is not int or horizon < 1:
        raise ValueError("invalid_windows")
    result = rolling_excess_returns(stock_rows, spy_rows, horizons=(horizon,))
    stock = {row["date"]: Decimal(str(row["close"])) for row in stock_rows}
    spy = {row["date"]: Decimal(str(row["close"])) for row in spy_rows}
    dates = sorted(stock.keys() & spy.keys())
    labels = {(x["start_session"], x["horizon"]): x for x in result["observations"]}
    observations = []
    for i in range(lookback, len(dates) - horizon):
        today, prior = dates[i], dates[i - lookback]
        past_stock = stock[today] / stock[prior] - 1
        past_spy = spy[today] / spy[prior] - 1
        past_excess = (past_stock - past_spy) * 100
        future = labels[(today, horizon)]
        observations.append({
            "signal_session": today,
            "past_excess_percentage_points": str(past_excess),
            "signal_positive_past_excess": past_excess > 0,
            "future_excess_percentage_points": future["excess_percentage_points"],
            "future_end_session": future["end_session"]})
    if not observations:
        raise ValueError("insufficient_signal_windows")
    return {"baseline": "past_relative_momentum", "lookback": lookback, "horizon": horizon,
            "observations": observations, "in_sample_only": True,
            "predictive_skill_established": False, "trade_ready": False}
