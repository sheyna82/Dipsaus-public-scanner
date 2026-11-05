"""Offline integrity verification for downloaded market data bytes.

Requires caller-provided bytes; never downloads, trusts, or executes content.
"""
import hashlib
from research_event_market_provenance import audit_market_observation


def verify_market_payload(record, payload, as_of_timestamp_utc):
    """Recompute SHA256 of raw bytes; authenticity is not established."""
    envelope = audit_market_observation(record, as_of_timestamp_utc)
    if not isinstance(payload, bytes):
        raise ValueError("market_payload_must_be_bytes")
    if not payload or len(payload) > 5_000_000:
        raise ValueError("market_payload_size_invalid")
    digest = hashlib.sha256(payload).hexdigest()
    if digest != record["content_sha256"]:
        raise ValueError("market_payload_digest_mismatch")
    return {
        **envelope,
        "digest_recomputed_against_source": True,
        "digest_matches_supplied_payload": True,
        "source_authenticity_verified": False,
        "price_data_semantics_verified": False,
        "predictive_skill_established": False,
        "trade_ready": False,
    }
