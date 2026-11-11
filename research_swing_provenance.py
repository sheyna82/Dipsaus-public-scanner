"""Research-only independent source timestamp and immutable identity checks.

This module validates the *shape* and chronology of externally supplied
research records. It does not authenticate a market-data provider, establish
the trustworthiness of claimed timestamps, or certify a historical backtest.
"""
from datetime import datetime, timezone
from hashlib import sha256
import json


def _instant(value):
    if not isinstance(value, str) or not value:
        raise ValueError("invalid_timestamp")
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        raise ValueError("invalid_timestamp") from None
    if dt.tzinfo is None or dt.utcoffset() is None:
        raise ValueError("timestamp_must_be_timezone_aware")
    return dt.astimezone(timezone.utc)


def verify_research_provenance(record):
    """Require signal creation and score-source data no later than entry.

    outcome source data must arrive after entry. SHA-256 digest allows later
    tamper detection *if* the digest is stored separately in immutable storage.
    """
    if not isinstance(record, dict):
        raise ValueError("invalid_record")
    required = ("ticker", "source_id", "strategy_version", "signal_id",
                "signal_created_at", "score_source_available_at",
                "entry_at", "outcome_source_available_at", "score")
    if any(key not in record for key in required):
        raise ValueError("missing_provenance_field")
    if any(not isinstance(record[k], str) or not record[k].strip()
           for k in ("ticker", "source_id", "strategy_version", "signal_id")):
        raise ValueError("invalid_identity")
    from decimal import Decimal, InvalidOperation
    try:
        if isinstance(record["score"], bool):
            raise ValueError("invalid_score")
        score = Decimal(str(record["score"]))
    except (InvalidOperation, ValueError, TypeError):
        raise ValueError("invalid_score") from None
    if not score.is_finite():
        raise ValueError("invalid_score")
    created = _instant(record["signal_created_at"])
    source = _instant(record["score_source_available_at"])
    entry = _instant(record["entry_at"])
    outcome = _instant(record["outcome_source_available_at"])
    if not (source <= created <= entry < outcome):
        raise ValueError("future_information_or_invalid_order")
    # Only allow deterministic JSON data, not arbitrary serialized objects.
    try:
        canonical = json.dumps(record, sort_keys=True, separators=(",", ":"),
                               ensure_ascii=True, allow_nan=False)
    except (TypeError, ValueError):
        raise ValueError("noncanonical_record") from None
    return {"research_only": True, "timestamps_structurally_valid": True,
            "provider_timestamps_independently_authenticated": False,
            "record_sha256": sha256(canonical.encode("utf-8")).hexdigest()}
