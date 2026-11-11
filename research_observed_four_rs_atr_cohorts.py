"""Observe RS/ATR cohorts on four existing frozen-event research symbols.

Unverified public Yahoo history, no strategy selection, no trading advice.
"""
import json
from research_probe_alternative_daily_source import SYMBOLS
from research_observed_four_event_spy_risk import fetch_payload, bars_from_payload
from dipsaus_offline_rs_atr_cohorts import compare_rs_atr_cohorts


def evaluate_observed_cohorts(symbol, stock_payload, spy_payload, *, now_utc=None):
    if symbol not in SYMBOLS:
        return {"symbol": symbol, "status": "DATA_BLOCKED", "reason": "unapproved_symbol"}
    stock = bars_from_payload(symbol, stock_payload, now_utc=now_utc)
    spy = bars_from_payload("SPY", spy_payload, now_utc=now_utc)
    if stock is None or spy is None:
        return {"symbol": symbol, "status": "DATA_BLOCKED", "reason": "source_quality"}
    result = compare_rs_atr_cohorts(stock, spy, min_per_cohort=10)
    return {"symbol": symbol, **result, "observed_source": "unverified_yahoo_daily",
            "earnings_asof_verified": False, "corporate_actions_verified": False,
            "trade_ready": False}


if __name__ == "__main__":
    try:
        spy = fetch_payload("SPY")
    except (OSError, ValueError, TimeoutError, UnicodeError, TypeError):
        spy = None
    for symbol in SYMBOLS:
        try:
            if spy is None:
                raise ValueError("spy_unavailable")
            result = evaluate_observed_cohorts(symbol, fetch_payload(symbol), spy)
        except (OSError, ValueError, TimeoutError, UnicodeError, TypeError):
            result = {"symbol": symbol, "status": "DATA_BLOCKED", "reason": "fetch_failed"}
        print(json.dumps(result, sort_keys=True))
