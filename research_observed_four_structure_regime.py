"""Observe predeclared structure/regime factors on the four research symbols."""
import json
from research_probe_alternative_daily_source import SYMBOLS
from research_observed_four_event_spy_risk import fetch_payload, bars_from_payload
from dipsaus_offline_structure_regime_diagnostic import evaluate_structure_regime


def evaluate_observed_structure(symbol, stock_payload, spy_payload, *, now_utc=None):
    if symbol not in SYMBOLS:
        return {"symbol": symbol, "status": "DATA_BLOCKED", "reason": "unapproved_symbol", "trade_ready": False}
    stock = bars_from_payload(symbol, stock_payload, now_utc=now_utc)
    spy = bars_from_payload("SPY", spy_payload, now_utc=now_utc)
    if stock is None or spy is None or [x["date"] for x in stock] != [x["date"] for x in spy]:
        return {"symbol": symbol, "status": "DATA_BLOCKED", "reason": "source_quality_or_alignment", "trade_ready": False}
    return {"symbol": symbol, **evaluate_structure_regime(stock, spy),
            "observed_source": "unverified_yahoo_daily",
            "corporate_actions_verified": False, "earnings_asof_verified": False,
            "trade_ready": False}


if __name__ == "__main__":
    try:
        spy = fetch_payload("SPY")
    except (OSError, ValueError, TimeoutError, UnicodeError, TypeError, KeyError):
        spy = None
    for symbol in SYMBOLS:
        try:
            if spy is None:
                raise ValueError("spy_unavailable")
            result = evaluate_observed_structure(symbol, fetch_payload(symbol), spy)
        except (OSError, ValueError, TimeoutError, UnicodeError, TypeError, KeyError):
            result = {"symbol": symbol, "status": "DATA_BLOCKED", "reason": "fetch_failed", "trade_ready": False}
        print(json.dumps(result, sort_keys=True))
