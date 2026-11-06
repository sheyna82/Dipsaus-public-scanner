"""Fail-closed chronology assessment for historical source evidence.

Retrieval after an entry does not prove pre-entry availability. A purported
pre-entry timestamp supplied by a caller is only a claim, not an independently
verified timestamp authority.
"""
from datetime import datetime, timezone


def _instant(value):
    if not isinstance(value, str) or not value.strip():
        raise ValueError("INVALID_EVIDENCE_TIMESTAMP")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("INVALID_EVIDENCE_TIMESTAMP") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("NAIVE_EVIDENCE_TIMESTAMP")
    return parsed.astimezone(timezone.utc)


def assess_historical_source_chronology(entry_at, retrieved_at, claimed_public_at=None):
    entry = _instant(entry_at)
    retrieved = _instant(retrieved_at)
    claimed = _instant(claimed_public_at) if claimed_public_at is not None else None
    if retrieved > datetime.now(timezone.utc):
        raise ValueError("FUTURE_RETRIEVAL_TIMESTAMP")
    if claimed is not None and claimed > retrieved:
        raise ValueError("PUBLICATION_CLAIM_AFTER_RETRIEVAL")
    retrieved_before_entry = retrieved < entry
    claimed_before_entry = claimed is not None and claimed < entry
    return {
        "schema": "historical_source_chronology_v1",
        "retrieval_precedes_entry": retrieved_before_entry,
        "claimed_publication_precedes_entry": claimed_before_entry,
        "timestamp_claims_independently_authenticated": False,
        "historical_publication_independently_proven": False,
        "eligible_for_backtest_performance_claim": False,
        "trade_ready": False,
        "classification": (
            "SUPPLIED_PRE_ENTRY_RETRIEVAL_CLAIM_UNVERIFIED"
            if retrieved_before_entry else
            "POST_ENTRY_RETRIEVAL_CANNOT_ESTABLISH_PRE_ENTRY_AVAILABILITY"
        ),
        "limitation": (
            "Caller-provided timestamps and retrieval receipts require "
            "independent authentication before historical promotion."
        ),
    }
