"""Offline outcome arithmetic for a frozen event snapshot.

Only explicitly supplied, independently sourced session observations can be
scored. This module neither fetches prices nor claims predictive skill.
"""
from decimal import Decimal, InvalidOperation
from datetime import date
from research_event_snapshot_gate import audit_event_snapshot

HORIZONS = (1, 3, 5)


def calculate_event_outcomes(snapshot, stock_sessions, benchmark_sessions):
    """Compute benchmark-relative close-to-close returns at matching sessions.

    Both series must have the same strictly ordered session dates. Event-day
    close is not silently included: supplied sessions must follow event date.
    """
    if not snapshot.get("snapshot_temporally_valid"):
        raise ValueError("snapshot_not_accepted")
    if snapshot.get("source_authenticity_verified") is not False:
        raise ValueError("snapshot_source_status_not_conservative")
    if len(stock_sessions) != len(benchmark_sessions):
        raise ValueError("outcome_session_length_mismatch")
    if len(stock_sessions) < max(HORIZONS):
        raise ValueError("insufficient_followup_sessions")
    event_date = date.fromisoformat(snapshot["event_date"])
    previous = None
    results = {}
    for i, (stock, benchmark) in enumerate(zip(stock_sessions, benchmark_sessions), 1):
        if stock["date"] != benchmark["date"]:
            raise ValueError("outcome_session_date_mismatch")
        current = date.fromisoformat(stock["date"])
        if current <= event_date or (previous is not None and current <= previous):
            raise ValueError("outcome_sessions_not_ordered_after_event")
        previous = current
        try:
            sp = Decimal(str(stock["close"]))
            bp = Decimal(str(benchmark["close"]))
        except (InvalidOperation, TypeError, ValueError) as exc:
            raise ValueError("invalid_outcome_close") from exc
        if not sp.is_finite() or not bp.is_finite() or sp <= 0 or bp <= 0:
            raise ValueError("invalid_outcome_close")
        if i in HORIZONS:
            base_stock = Decimal(snapshot["close_price"])
            base_benchmark = Decimal(snapshot["benchmark_close"])
            stock_return = sp / base_stock - 1
            benchmark_return = bp / base_benchmark - 1
            results[i] = {
                "session_date": current.isoformat(),
                "stock_return": str(stock_return),
                "benchmark_return": str(benchmark_return),
                "excess_return": str(stock_return - benchmark_return),
            }
    return {
        "symbol": snapshot["symbol"],
        "event_date": snapshot["event_date"],
        "horizons": results,
        "synthetic_or_supplied_data_only": True,
        "market_data_provenance_verified": False,
        "exchange_calendar_verified": False,
        "predictive_skill_established": False,
        "trade_ready": False,
    }
