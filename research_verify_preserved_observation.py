"""Verify a committed research observation against a separately recorded byte hash.

This is an offline provenance check, not independent provider authentication.
"""
import hashlib
from pathlib import Path
from research_verify_finnhub_observation import verify

def verify_preserved_observation(path, *, expected_json_sha256, expected_source_sha256):
    if not isinstance(expected_json_sha256, str) or len(expected_json_sha256) != 64:
        raise ValueError("invalid_expected_json_digest")
    if not isinstance(expected_source_sha256, str) or len(expected_source_sha256) != 64:
        raise ValueError("invalid_expected_source_digest")
    try:
        int(expected_json_sha256, 16)
        int(expected_source_sha256, 16)
    except ValueError as exc:
        raise ValueError("invalid_expected_digest") from exc
    data = Path(path).read_bytes()
    if len(data) > 8192:
        raise ValueError("observation_too_large")
    digest = hashlib.sha256(data).hexdigest()
    if digest != expected_json_sha256.lower():
        raise ValueError("observation_json_hash_mismatch")
    result = verify(path)
    if result["source_sha256"] != expected_source_sha256.lower():
        raise ValueError("observation_source_hash_mismatch")
    return {"status":"preserved_bytes_and_source_integrity_verified",
            "observation_json_sha256":digest,
            "source_sha256":result["source_sha256"],
            "symbol":result["symbol"],
            "provider_authenticated":False,
            "quote_accuracy_verified":False,
            "prospective_signal_proven":False,
            "trade_ready":False}
