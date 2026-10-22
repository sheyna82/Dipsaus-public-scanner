"""Sensitivity of chronological RS/ATR diagnostics to minimum test size.

This does not retune thresholds or select a best filter. Smaller cohorts are
reported as descriptive only, never as independent predictive validation.
"""
import json
from research_probe_alternative_daily_source import SYMBOLS
from research_observed_four_event_spy_risk import fetch_payload, bars_from_payload
from dipsaus_offline_chronological_rs_atr import chronological_rs_atr_diagnostic


def evaluate_sensitivity(symbol, stock_payload, spy_payload, *, now_utc=None):
    if symbol not in SYMBOLS:
        return {"symbol": symbol, "status": "DATA_BLOCKED", "reason": "unapproved_symbol", "trade_ready": False}
    stock = bars_from_payload(symbol, stock_payload, now_utc=now_utc)
    spy = bars_from_payload("SPY", spy_payload, now_utc=now_utc)
    if stock is None or spy is None or [b["date"] for b in stock] != [b["date"] for b in spy]:
        return {"symbol": symbol, "status": "DATA_BLOCKED", "reason": "source_quality_or_alignment", "trade_ready": False}
    results = {}
    for minimum in (5, 10, 15):
        results[str(minimum)] = chronological_rs_atr_diagnostic(stock, spy, min_test=minimum)
    return {"symbol": symbol, "status": "DESCRIPTIVE_SENSITIVITY_ONLY",
            "minimum_test_event_scenarios": results,
            "thresholds_retuned": False, "independent_untouched_holdout": False,
            "predictive_edge_proven": False, "trade_ready": False}


if __name__ == "__main__":
    try:
        spy = fetch_payload("SPY")
    except (OSError, ValueError, TimeoutError, UnicodeError, TypeError, KeyError):
        spy = None
    for symbol in SYMBOLS:
        try:
            if spy is None:
                raise ValueError("spy_unavailable")
            result = evaluate_sensitivity(symbol, fetch_payload(symbol), spy)
        except (OSError, ValueError, TimeoutError, UnicodeError, TypeError, KeyError):
            result = {"symbol": symbol, "status": "DATA_BLOCKED", "reason": "fetch_failed", "trade_ready": False}
        print(json.dumps(result, sort_keys=True))
