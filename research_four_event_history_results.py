"""Research-only four-symbol observed-history evaluation (no earnings inference).

Uses actual fetched Yahoo daily bars, applies strict OHLCV validation,
predeclared 10-session nonoverlapping signal outcomes, and reports sample
limitations. Does not store prices, alert, or change live scanner.
"""
import json
from datetime import datetime, timezone
from urllib.request import Request, urlopen
from research_probe_alternative_daily_source import BASE, SYMBOLS
from research_audit_four_event_ohlcv import audit_chart
from dipsaus_offline_event_history_outcomes import evaluate_daily_event_history
from dipsaus_offline_event_calendar_baseline import compare_calendar_baseline
from dipsaus_offline_completed_daily_bar_gate import completed_daily_bars


def evaluate_payload(symbol, payload):
    audit = audit_chart(payload, symbol)
    if audit["status"] != "OHLCV_VALIDATED":
        return audit
    result = payload["chart"]["result"][0]
    quote = result["indicators"]["quote"][0]
    bars = []
    for i, ts in enumerate(result["timestamp"]):
        bars.append({"date": datetime.fromtimestamp(ts, timezone.utc).date().isoformat(),
                     **{field: quote[field][i] for field in
                        ("open", "high", "low", "close", "volume")}})
    gate = completed_daily_bars(bars, now_utc=datetime.now(timezone.utc))
    if gate['status'] != 'PRIOR_DATE_ONLY':
        return {'symbol': symbol, 'status': 'DATA_BLOCKED', 'reason': gate['reason']}
    bars = gate['rows']
    outcomes = evaluate_daily_event_history(bars, horizon=10, fee_bps_each_side=10)
    baseline = compare_calendar_baseline(bars, horizon=10, fee_bps_each_side=10)
    return {"symbol": symbol, "status": outcomes["status"],
            "history_bars": len(bars), "signal_count": outcomes.get("sample_count"),
            "positive_terminal_count": outcomes.get("positive_terminal_count"),
            "severe_terminal_loss_count": outcomes.get("severe_terminal_loss_count"),
            "severe_intraperiod_drawdown_count": outcomes.get("severe_intraperiod_drawdown_count"),
            "mean_terminal_net_pct": outcomes.get("mean_terminal_net_pct"),
            "signal_dates": [x["signal_date"] for x in outcomes.get("outcomes", [])],
            "calendar_baseline": baseline,
            "earnings_dates_verified": False, "independent_holdout": False,
            "predictive_edge_proven": False, "trade_ready": False}


def evaluate_symbol(symbol):
    try:
        with urlopen(Request(BASE.format(symbol=symbol),
                             headers={"User-Agent": "Mozilla/5.0"}), timeout=12) as response:
            raw = response.read(300_001)
        if len(raw) > 300_000:
            return {"symbol": symbol, "status": "DATA_BLOCKED", "reason": "oversized"}
        return evaluate_payload(symbol, json.loads(raw))
    except (OSError, ValueError, TimeoutError, UnicodeError):
        return {"symbol": symbol, "status": "DATA_BLOCKED", "reason": "fetch_failed"}


if __name__ == "__main__":
    for symbol in SYMBOLS:
        print(json.dumps(evaluate_symbol(symbol), sort_keys=True))
