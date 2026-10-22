"""Observed, non-tradable same-date market comparison of frozen event signals.

Public Yahoo OHLCV is unverified; missing or misaligned sessions fail closed.
No portfolio positions, notifications, secrets or live code are accessed.
"""
import json
from datetime import datetime, timezone
from urllib.request import Request, urlopen
from research_four_event_long_history import LONG_BASE
from research_probe_alternative_daily_source import SYMBOLS
from research_audit_four_event_ohlcv import audit_chart
from dipsaus_offline_completed_daily_bar_gate import completed_daily_bars
from dipsaus_offline_frozen_event_market_bridge import evaluate_frozen_events_against_market
from dipsaus_offline_chronological_matched_risk import chronological_matched_risk


def bars_from_payload(symbol, payload, *, now_utc=None):
    audit = audit_chart(payload, symbol)
    if audit.get("status") != "OHLCV_VALIDATED":
        return None
    result = payload["chart"]["result"][0]
    quote = result["indicators"]["quote"][0]
    bars = [{"date": datetime.fromtimestamp(ts, timezone.utc).date().isoformat(),
             **{k: quote[k][i] for k in ("open", "high", "low", "close", "volume")}}
            for i, ts in enumerate(result["timestamp"])]
    gate = completed_daily_bars(bars, now_utc=now_utc or datetime.now(timezone.utc))
    return gate["rows"] if gate.get("status") == "PRIOR_DATE_ONLY" else None


def evaluate_observed_pair(symbol, stock_payload, spy_payload, *, now_utc=None):
    if symbol not in SYMBOLS:
        return {"symbol": symbol, "status": "DATA_BLOCKED", "reason": "unapproved_symbol"}
    stock = bars_from_payload(symbol, stock_payload, now_utc=now_utc)
    spy = bars_from_payload("SPY", spy_payload, now_utc=now_utc)
    if stock is None or spy is None:
        return {"symbol": symbol, "status": "DATA_BLOCKED", "reason": "source_quality"}
    if [r["date"] for r in stock] != [r["date"] for r in spy]:
        return {"symbol": symbol, "status": "DATA_BLOCKED", "reason": "unaligned_sessions",
                "stock_bars": len(stock), "spy_bars": len(spy)}
    result = evaluate_frozen_events_against_market(stock, spy)
    result['chronological_diagnostic'] = chronological_matched_risk(stock, spy)
    return {"symbol": symbol, **result, "observed_source": "unverified_yahoo_daily",
            "corporate_actions_verified": False, "earnings_asof_verified": False,
            "survivorship_free": False, "trade_ready": False}


def fetch_payload(symbol):
    url = LONG_BASE.format(symbol=symbol)
    with urlopen(Request(url, headers={"User-Agent": "Mozilla/5.0"}), timeout=12) as response:
        raw = response.read(900001)
    if len(raw) > 900000:
        raise ValueError("oversized")
    return json.loads(raw)


if __name__ == "__main__":
    try:
        spy = fetch_payload("SPY")
    except (OSError, ValueError, TimeoutError, UnicodeError):
        spy = None
    for symbol in SYMBOLS:
        try:
            if spy is None:
                raise ValueError("spy_unavailable")
            result = evaluate_observed_pair(symbol, fetch_payload(symbol), spy)
        except (OSError, ValueError, TimeoutError, UnicodeError, TypeError):
            result = {"symbol": symbol, "status": "DATA_BLOCKED", "reason": "fetch_failed"}
        result.pop("rows", None)
        print(json.dumps(result, sort_keys=True))
