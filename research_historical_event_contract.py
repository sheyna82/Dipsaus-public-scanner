"""Research-only, offline, privacy-preserving historical event contract.

Validates metadata only. No ticker, holding, price, broker quote, token or
personal data is accepted. Does not write files or authorize trading.
"""
from datetime import datetime, timezone
import math

BLOCKED = {"trade_ready": False, "order_placement_enabled": False,
           "source_authenticity_independently_verified": False}
COMMON = {"schema_version", "event_id", "candidate_id", "observed_utc",
          "event_type", "source_digest"}
SIGNAL = COMMON | {"decision", "feature_digest"}
OUTCOME = COMMON | {"return_pct", "horizon_sessions"}
FORBIDDEN = {"symbol", "ticker", "name", "isin", "holdings", "shares", "bid",
             "ask", "price", "broker", "token", "secret", "account", "email",
             "raw_report", "portfolio"}

def _timestamp(value):
    if not isinstance(value, str):
        return None
    try:
        t = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return t.astimezone(timezone.utc) if t.tzinfo is not None else None
    except ValueError:
        return None

def validate_historical_events(events):
    if not isinstance(events, list):
        return {**BLOCKED, "status": "EVENT_CONTRACT_BLOCKED", "reason": "NOT_A_LIST"}
    seen = set()
    signals = {}
    outcomes = {}
    for event in events:
        if not isinstance(event, dict):
            return {**BLOCKED, "status": "EVENT_CONTRACT_BLOCKED", "reason": "INVALID_EVENT"}
        kind = event.get("event_type")
        expected = SIGNAL if kind == "SIGNAL" else OUTCOME if kind == "OUTCOME" else None
        if expected is None or set(event) != expected or set(event) & FORBIDDEN:
            return {**BLOCKED, "status": "EVENT_CONTRACT_BLOCKED",
                    "reason": "UNKNOWN_TYPE_OR_FIELDS"}
        if event["schema_version"] != 1:
            return {**BLOCKED, "status": "EVENT_CONTRACT_BLOCKED", "reason": "SCHEMA_VERSION"}
        for key in ("event_id", "candidate_id", "source_digest"):
            value = event[key]
            if not isinstance(value, str) or not value.strip() or len(value) > 128:
                return {**BLOCKED, "status": "EVENT_CONTRACT_BLOCKED",
                        "reason": "INVALID_IDENTIFIER"}
        if event["event_id"] in seen:
            return {**BLOCKED, "status": "EVENT_CONTRACT_BLOCKED",
                    "reason": "DUPLICATE_EVENT"}
        seen.add(event["event_id"])
        timestamp = _timestamp(event["observed_utc"])
        if timestamp is None:
            return {**BLOCKED, "status": "EVENT_CONTRACT_BLOCKED",
                    "reason": "INVALID_TIMESTAMP"}
        cid = event["candidate_id"]
        if kind == "SIGNAL":
            if cid in signals or event["decision"] not in ("SELECTED", "REJECTED", "DEFERRED"):
                return {**BLOCKED, "status": "EVENT_CONTRACT_BLOCKED",
                        "reason": "DUPLICATE_OR_INVALID_SIGNAL"}
            if not isinstance(event["feature_digest"], str) or len(event["feature_digest"]) != 64 or any(c not in "0123456789abcdef" for c in event["feature_digest"]):
                return {**BLOCKED, "status": "EVENT_CONTRACT_BLOCKED",
                        "reason": "INVALID_FEATURE_DIGEST"}
            signals[cid] = timestamp
        else:
            if cid in outcomes or type(event["return_pct"]) not in (int, float) or not math.isfinite(event["return_pct"]) or type(event["horizon_sessions"]) is not int or event["horizon_sessions"] < 1:
                return {**BLOCKED, "status": "EVENT_CONTRACT_BLOCKED",
                        "reason": "DUPLICATE_OR_INVALID_OUTCOME"}
            outcomes[cid] = timestamp
    if any(cid not in signals or at <= signals[cid] for cid, at in outcomes.items()):
        return {**BLOCKED, "status": "EVENT_CONTRACT_BLOCKED",
                "reason": "ORPHAN_OR_NONFUTURE_OUTCOME"}
    return {**BLOCKED, "status": "HISTORICAL_EVENT_CONTRACT_RESEARCH_ONLY",
            "signal_count": len(signals), "outcome_count": len(outcomes),
            "missing_outcome_count": len(set(signals) - set(outcomes)),
            "archive_completeness_verified": False,
            "digest_authenticity_verified": False,
            "note": "Digests and opaque IDs do not prove privacy or source authenticity; no persistence."}
