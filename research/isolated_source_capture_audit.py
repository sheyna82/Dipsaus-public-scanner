"""Independent research source-byte gate; hashes prove identity, not authenticity."""
import hashlib
from datetime import datetime, timezone

def verify_source_capture(*, raw_bytes, expected_sha256, captured_at,
                          source_available_at, decision_at):
    if not isinstance(raw_bytes, bytes) or not raw_bytes:
        raise ValueError("MISSING_SOURCE_BYTES")
    if not isinstance(expected_sha256, str) or len(expected_sha256) != 64:
        raise ValueError("INVALID_SOURCE_DIGEST")
    actual = hashlib.sha256(raw_bytes).hexdigest()
    if actual != expected_sha256.lower():
        raise ValueError("SOURCE_BYTES_MISMATCH")
    def stamp(s):
        if not isinstance(s, str):
            raise ValueError("INVALID_SOURCE_TIME")
        try:
            dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
        except ValueError as exc:
            raise ValueError("INVALID_SOURCE_TIME") from exc
        if dt.tzinfo is None:
            raise ValueError("NAIVE_SOURCE_TIME")
        return dt.astimezone(timezone.utc)
    capture, available, decision = map(stamp, (captured_at, source_available_at, decision_at))
    if available > capture or capture > decision:
        raise ValueError("SOURCE_NOT_AVAILABLE_AT_DECISION")
    return {"sha256_verified": True, "chronology_claims_consistent": True,
            "external_publication_time_independently_proven": False,
            "source_authenticity_independently_proven": False,
            "trade_ready": False}
