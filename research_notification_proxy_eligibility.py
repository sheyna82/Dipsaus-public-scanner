"""Research-only eligibility gate for dated notification forward-return proxies.

A completed proxy is not an independently verified execution or a trade P&L.
This gate explicitly refuses to promote proxy outcomes to verified trades.
"""
from datetime import date
from math import isfinite

def audit_notification_proxy_outcomes(signal_day, forward_by_symbol, horizons=(3, 5, 10, 20)):
    try:
        day = date.fromisoformat(signal_day)
    except (TypeError, ValueError):
        raise ValueError("invalid_signal_day") from None
    if not isinstance(forward_by_symbol, dict):
        raise ValueError("invalid_forward_results")
    rows = []
    for symbol, outcomes in sorted(forward_by_symbol.items()):
        if not isinstance(symbol, str) or not symbol or not isinstance(outcomes, dict):
            raise ValueError("invalid_symbol_outcomes")
        for horizon in horizons:
            if type(horizon) is not int or horizon < 1:
                raise ValueError("invalid_horizon")
            outcome = outcomes.get(horizon)
            if outcome is None:
                rows.append({"symbol": symbol, "horizon": horizon, "status": "missing_future_sessions",
                             "net_proxy_return_pct": None})
                continue
            if not isinstance(outcome, dict) or outcome.get("research_only") is not True or outcome.get("execution_verified") is not False:
                raise ValueError("untrusted_or_execution_claimed_outcome")
            try:
                entry, exit_ = date.fromisoformat(outcome["entry_date"]), date.fromisoformat(outcome["exit_date"])
            except (ValueError, TypeError, KeyError):
                raise ValueError("invalid_outcome_dates") from None
            if not (day < entry <= exit_):
                raise ValueError("outcome_before_signal")
            net = outcome.get("net_proxy_return_pct")
            if isinstance(net, bool) or not isinstance(net, (float, int)) or not isfinite(net):
                raise ValueError("invalid_proxy_return")
            rows.append({"symbol": symbol, "horizon": horizon, "status": "research_proxy_only",
                         "net_proxy_return_pct": net, "entry_date": entry.isoformat(),
                         "exit_date": exit_.isoformat()})
    return {"research_only": True, "trade_ready": False, "execution_verified": False,
            "verified_trade_count": 0, "proxy_count": sum(x["status"] == "research_proxy_only" for x in rows),
            "missing_count": sum(x["status"] == "missing_future_sessions" for x in rows),
            "rows": rows}
