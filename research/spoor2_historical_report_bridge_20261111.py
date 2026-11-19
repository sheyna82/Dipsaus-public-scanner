"""Read-only Spoor 2 bridge from historical candidate dossiers to isolated research.

Never imports notification transport or production execution code. It cannot
create verified entry signals or orders. Input must be a historical dossier.
"""
from research.spoor2_candidate_levels_20261111 import research_levels
from research.spoor2_notification_policy_20261111 import (
    classify_notification, notification_subject,
)


def analyze_candidate(candidate, *, reference_price=None):
    """Build a non-executable, audit-friendly preview from an existing dossier."""
    if not isinstance(candidate, dict):
        return {"status": "UNKNOWN", "trade_ready": False, "notification_channel": "NONE"}
    symbol = candidate.get("symbol")
    if not isinstance(symbol, str) or not symbol.strip():
        return {"status": "UNKNOWN", "trade_ready": False, "notification_channel": "NONE"}
    history = candidate.get("recovery_map")
    price = reference_price if reference_price is not None else candidate.get("last_close_usd")
    levels = research_levels(history, price)
    # Deliberately do not inherit candidate.trade_ready or phase: a historical
    # research row is not independent, time-fresh broker verification.
    classification = classify_notification({"phase": "BREAKOUT-SEEN"})
    return {
        "symbol": symbol,
        "status": levels["status"],
        "levels": levels,
        "notification_channel": classification["channel"],
        "notification_subject": notification_subject(symbol, classification),
        "trade_ready": False,
        "order_placement_enabled": False,
        "source": "HISTORICAL_CANDIDATE_ONLY",
    }


def analyze_report(report):
    """Transform candidate rows in memory; no disk writes, network or ntfy."""
    if not isinstance(report, dict) or not isinstance(report.get("candidates"), list):
        return {"status": "UNKNOWN", "rows": [], "trade_ready": False}
    rows = [analyze_candidate(c) for c in report["candidates"]]
    return {"status": "RESEARCH_PREVIEW", "rows": rows, "trade_ready": False}
