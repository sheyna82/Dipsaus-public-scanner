"""Causal, descriptive daily-event recovery outcomes on validated historical bars.

Predeclared signal: two increasing closes and close above previous five-close
mean; downside warning: <=-3% daily or >2x prior 14-session average range.
Non-overlapping signals; next-open entry, 10-session terminal close, 10 bps
per side. Severe terminal loss <=-3%. No earnings calendar or predictive claim.
"""
from dipsaus_offline_ohlcv_features import _valid


def evaluate_daily_event_history(rows, *, horizon=10, fee_bps_each_side=10):
    if not _valid(rows) or type(horizon) is not int or horizon < 1 or horizon > 30:
        return {"status": "DATA_BLOCKED", "reason": "invalid_history_or_horizon"}
    if type(fee_bps_each_side) not in (int, float) or not 0 <= fee_bps_each_side <= 100:
        return {"status": "DATA_BLOCKED", "reason": "invalid_cost"}
    outcomes = []
    # Signal formed only after bar i closes. Execution is next session open.
    i = 21
    while i + horizon < len(rows):
        last = rows[i]
        trend = (rows[i - 2]["close"] < rows[i - 1]["close"] < last["close"]
                 and last["close"] > sum(x["close"] for x in rows[i - 5:i]) / 5)
        prior = rows[i - 1]["close"]
        mean_range = sum(x["high"] - x["low"] for x in rows[i - 14:i]) / 14
        risk = (last["close"] / prior - 1 <= -0.03 or
                last["high"] - last["low"] > 2 * mean_range)
        if not trend or risk:
            i += 1
            continue
        entry = rows[i + 1]["open"]
        exit_close = rows[i + horizon]["close"]
        net = 100 * (exit_close / entry - 1) - 2 * fee_bps_each_side / 100
        min_low = min(x["low"] for x in rows[i + 1:i + horizon + 1])
        drawdown = 100 * (min_low / entry - 1)
        outcomes.append({"signal_date": last["date"],
                         "terminal_return_net_pct": round(net, 5),
                         "max_adverse_excursion_pct": round(min(0, drawdown), 5),
                         "severe_terminal_loss": net <= -3,
                         "severe_intraperiod_drawdown": drawdown <= -3})
        i += horizon + 1
    count = len(outcomes)
    return {"status": "DESCRIPTIVE_HISTORY", "sample_count": count,
            "positive_terminal_count": sum(x["terminal_return_net_pct"] > 0 for x in outcomes),
            "severe_terminal_loss_count": sum(x["severe_terminal_loss"] for x in outcomes),
            "severe_intraperiod_drawdown_count": sum(x["severe_intraperiod_drawdown"] for x in outcomes),
            "mean_terminal_net_pct": (round(sum(x["terminal_return_net_pct"] for x in outcomes) / count, 5)
                                      if count else None),
            "outcomes": outcomes, "earnings_calendar_verified": False,
            "survivorship_bias_audited": False, "predictive_edge_proven": False,
            "trade_ready": False}
