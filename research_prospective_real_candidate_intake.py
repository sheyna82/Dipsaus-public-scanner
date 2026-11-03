"""Fail-closed boundary for prospective REAL candidate intake.

Does not fetch prices or imply independently authenticated market data.
Accepts only a frozen source observation and never creates a trading signal.
"""
import re
from datetime import date, datetime, timezone
from urllib.parse import urlsplit


def validate_prospective_observation(observation, *, now_utc):
    if not isinstance(observation, dict):
        raise ValueError("invalid_observation")
    if not isinstance(now_utc, datetime) or now_utc.tzinfo is None or now_utc.utcoffset() != timezone.utc.utcoffset(now_utc):
        raise ValueError("utc_clock_required")
    if observation.get("research_only") is not True or observation.get("trade_ready") is not False:
        raise ValueError("unsafe_observation")
    if observation.get("future_outcome") is not None:
        raise ValueError("future_outcome_forbidden")
    for key in ("symbol", "protocol_id", "signal_session", "source_name", "source_url", "source_observed_at_utc"):
        if not isinstance(observation.get(key), str) or not observation[key].strip():
            raise ValueError("missing_required_field_" + key)
    if not re.fullmatch(r"[A-Z0-9.\\-]{1,16}", observation["symbol"]):
        raise ValueError("invalid_symbol")
    try:
        signal_day = date.fromisoformat(observation["signal_session"])
        observed = datetime.fromisoformat(observation["source_observed_at_utc"].replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("invalid_source_time_or_session") from exc
    if observed.tzinfo is None or observed.utcoffset() != timezone.utc.utcoffset(observed):
        raise ValueError("source_time_must_be_utc")
    if observed > now_utc or signal_day > now_utc.date():
        raise ValueError("future_observation")
    url = urlsplit(observation["source_url"])
    if url.scheme != "https" or not url.hostname or url.username or url.password or url.fragment or url.query:
        raise ValueError("invalid_source_url")
    if observation.get("independent_source_authentication") is not False:
        raise ValueError("unsupported_source_authentication_claim")
    if observation.get("independent_timestamp_proof") is not False:
        raise ValueError("unsupported_timestamp_claim")
    return {
        "status": "observation_schema_accepted_unverified",
        "symbol": observation["symbol"],
        "signal_session": observation["signal_session"],
        "source_name": observation["source_name"],
        "source_url": observation["source_url"],
        "source_observed_at_utc_claimed": observed.isoformat(),
        "independent_source_authentication": False,
        "independent_timestamp_proof": False,
        "prospective_signal_proven": False,
        "research_only": True,
        "trade_ready": False,
    }
