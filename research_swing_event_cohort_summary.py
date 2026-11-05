"""Descriptive event outcome cohorts; never calibrated forecasts or trade signals."""
from math import isfinite
from statistics import mean, median


def summarize_event_cohort(records, *, horizon, minimum_events=20):
    """Summarize independent, non-overlapping event outcomes for one horizon.

    Records contain event_id, symbol, entry_index, exit_index and outcome.
    Session indices are only comparable within a symbol's own bar series.
    Reject overlapping holding periods per symbol to avoid pseudo-replication.
    """
    if type(horizon) is not int or horizon < 1:
        raise ValueError("invalid_horizon")
    if type(minimum_events) is not int or minimum_events < 2:
        raise ValueError("invalid_minimum_events")
    selected = []
    seen = set()
    last_exit = {}
    for row in sorted(records, key=lambda r: (r["symbol"], r["entry_index"])):
        if row["horizon"] != horizon:
            continue
        symbol, event_id = row["symbol"], row["event_id"]
        if not isinstance(symbol, str) or not symbol or not isinstance(event_id, str) or not event_id:
            raise ValueError("invalid_event_identity")
        key = (symbol, event_id)
        if key in seen:
            raise ValueError("duplicate_event")
        seen.add(key)
        entry, exit_ = row["entry_index"], row["exit_index"]
        if type(entry) is not int or type(exit_) is not int or entry < 0 or exit_ <= entry:
            raise ValueError("invalid_holding_window")
        if entry <= last_exit.get(symbol, -1):
            raise ValueError("overlapping_event_windows")
        last_exit[symbol] = exit_
        net = row["net_return_pct"]
        mae = row["worst_intratrade_excursion_pct"]
        if (type(net) not in (float, int) or type(mae) not in (float, int)
                or not isfinite(net) or not isfinite(mae)):
            raise ValueError("invalid_outcome")
        selected.append((net, mae))
    count = len(selected)
    result = {"horizon": horizon, "event_count": count,
              "minimum_events": minimum_events, "sufficient_sample": count >= minimum_events,
              "trade_ready": False}
    if count < minimum_events:
        return result
    returns = [r for r, _ in selected]
    excursions = [m for _, m in selected]
    result.update({
        "mean_net_return_pct": round(mean(returns), 4),
        "median_net_return_pct": round(median(returns), 4),
        "historical_loss_fraction": round(sum(r < 0 for r in returns) / count, 4),
        "historical_mae_below_minus_5_fraction": round(sum(m <= -5 for m in excursions) / count, 4),
        "worst_net_return_pct": round(min(returns), 4),
    })
    return result
