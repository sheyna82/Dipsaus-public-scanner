"""Research-only pre-outcome decision record builder; not connected to live scanning.

Caller must capture and persist records BEFORE future outcome data becomes available.
A self-reported timestamp and digest do not prove independent prospective capture.
"""
import hashlib
import json
from datetime import datetime, timezone


def decision_record(symbol, assessment, observed_at_utc, source="Yahoo daily OHLCV"):
    if not isinstance(symbol, str) or not symbol or not symbol.isascii():
        raise ValueError("INVALID_SYMBOL")
    if not isinstance(assessment, dict):
        raise ValueError("INVALID_ASSESSMENT")
    try:
        observed = datetime.fromisoformat(observed_at_utc.replace("Z", "+00:00"))
    except (ValueError, TypeError, AttributeError):
        raise ValueError("INVALID_OBSERVATION_TIME") from None
    if observed.tzinfo is None or observed.utcoffset().total_seconds() != 0:
        raise ValueError("OBSERVATION_TIME_NOT_UTC")
    bar_date = assessment.get("last_bar_date")
    if not isinstance(bar_date, str):
        raise ValueError("INVALID_BAR_DATE")
    try:
        last_bar = datetime.strptime(bar_date, "%Y-%m-%d").date()
    except ValueError:
        raise ValueError("INVALID_BAR_DATE") from None
    if last_bar > observed.date():
        raise ValueError("FUTURE_BAR_DATE")
    if type(assessment.get("pre_screen_match")) is not bool:
        raise ValueError("MISSING_SELECTION_DECISION")
    signals = assessment.get("signals")
    if not isinstance(signals, dict) or not signals or any(type(v) is not bool for v in signals.values()):
        raise ValueError("INVALID_SIGNALS")
    if not isinstance(source, str) or not source.strip():
        raise ValueError("INVALID_SOURCE")
    reasons = []
    if not assessment["pre_screen_match"]:
        if assessment.get("drawdown_pct") is None or assessment.get("rebound_from_low_pct") is None:
            raise ValueError("MISSING_REJECTION_FEATURES")
        if assessment["drawdown_pct"] > -20:
            reasons.append("DRAWDOWN_BELOW_THRESHOLD")
        if not 1.5 <= assessment["rebound_from_low_pct"] <= 35:
            reasons.append("REBOUND_OUTSIDE_RANGE")
        if not (assessment.get("early_turn") or assessment.get("established_turn") or assessment.get("signal_count", 0) >= 3):
            reasons.append("TURN_SIGNALS_INSUFFICIENT")
        if not reasons:
            raise ValueError("UNEXPLAINED_REJECTION")
    payload = {
        "schema_version": 1, "research_only": True, "trade_ready": False,
        "symbol": symbol, "observed_at_utc": observed.isoformat(),
        "last_bar_date": bar_date, "data_source": source,
        "selected": assessment["pre_screen_match"],
        "rejection_reasons": reasons,
        "features": {k: assessment[k] for k in (
            "drawdown_pct", "rebound_from_low_pct", "early_turn",
            "established_turn", "signal_count", "signals"
        ) if k in assessment},
        "prospective_capture_independently_verified": False,
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return {**payload, "sha256": hashlib.sha256(canonical.encode("utf-8")).hexdigest()}
