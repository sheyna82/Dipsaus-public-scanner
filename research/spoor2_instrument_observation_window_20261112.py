"""Offline freshness and replay policy for signed instrument observations.

Caller-supplied timestamps/nonces are claims, not proof of trusted issuance.
No stateful replay store is connected; never admit an observation for trading.
"""
from datetime import datetime, timezone


def audit_instrument_observation_window(observed_utc, verification_utc,
                                        challenge_nonce, *, max_age_seconds=300):
    base = {"status": "BLOCKED", "freshness_attested": False,
            "replay_prevented": False, "source_attested": False,
            "trade_ready": False, "order_placement_enabled": False}
    if type(max_age_seconds) is not int or not 1 <= max_age_seconds <= 3600:
        return {**base, "blocks": ["INVALID_INSTRUMENT_AGE_POLICY"]}
    if not isinstance(challenge_nonce, str) or not (
        32 <= len(challenge_nonce) <= 128
    ) or any(c not in "0123456789abcdef" for c in challenge_nonce):
        return {**base, "blocks": ["INSTRUMENT_CHALLENGE_INVALID"]}
    if (isinstance(observed_utc, str) and len(observed_utc) > 64 or
            isinstance(verification_utc, str) and len(verification_utc) > 64):
        return {**base, "blocks": ["INSTRUMENT_OBSERVATION_TIME_OVERSIZED"]}
    try:
        if not isinstance(observed_utc, str) or not isinstance(verification_utc, str):
            raise ValueError("missing timestamps")
        if not observed_utc.endswith("Z") or not verification_utc.endswith("Z"):
            raise ValueError("not explicit UTC")
        observed = datetime.fromisoformat(observed_utc.replace("Z", "+00:00"))
        verified = datetime.fromisoformat(verification_utc.replace("Z", "+00:00"))
        if (observed.tzinfo is None or verified.tzinfo is None or
            observed.utcoffset() != timezone.utc.utcoffset(observed) or
            verified.utcoffset() != timezone.utc.utcoffset(verified)):
            raise ValueError("not UTC")
    except (ValueError, TypeError, AttributeError, OverflowError):
        return {**base, "blocks": ["INSTRUMENT_OBSERVATION_TIME_INVALID"]}
    age = (verified - observed).total_seconds()
    if not 0 <= age <= max_age_seconds:
        return {**base, "blocks": ["INSTRUMENT_OBSERVATION_OUTSIDE_WINDOW"]}
    return {**base, "status": "TIME_WINDOW_CLAIMS_CONSISTENT_ONLY",
            "blocks": ["INSTRUMENT_CHALLENGE_ISSUANCE_NOT_ATTESTED",
                       "INSTRUMENT_NONCE_SINGLE_USE_NOT_ENFORCED",
                       "INSTRUMENT_TRUSTED_CLOCK_NOT_ATTESTED",
                       "INSTRUMENT_SIGNED_TIMESTAMP_BINDING_NOT_CONNECTED"]}
