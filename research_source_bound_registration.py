"""Research-only bridge: bind source bytes before immutable candidate registration.

The caller must separately retain the exact source bytes; the existing ledger
archive contains the digest but NOT the source response itself.
"""
import hashlib

from research_source_snapshot_binding import bind_source_snapshot
from research_real_observation_registration_bridge import register_validated_observation


def register_observation_with_source_snapshot(observation, source_bytes, directory, *, clock):
    if not isinstance(source_bytes, bytes) or not source_bytes:
        raise ValueError("missing_source_bytes")
    expected = hashlib.sha256(source_bytes).hexdigest()
    bound = bind_source_snapshot(observation, source_bytes, expected_sha256=expected)
    result = register_validated_observation(bound, directory, clock=clock)
    return {
        **result,
        "source_snapshot_sha256": expected,
        "source_bytes_archived": False,
        "source_bytes_independently_authenticated": False,
        "trade_ready": False,
    }
