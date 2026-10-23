"""Research-only provenance-aware cache identity and freshness checks.

No networking, persistence, trading or live notification changes.
"""

from datetime import datetime, timedelta


REQUIRED_IDENTITY = (
    "security_id", "market", "provider", "interval",
    "adjustment", "dataset_version",
)


def _aware(value):
    if not isinstance(value, str):
        raise ValueError("invalid_timestamp")
    try:
        result = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError("invalid_timestamp") from exc
    if result.tzinfo is None or result.utcoffset() is None:
        raise ValueError("timezone_required")
    return result


def assess_cached_observation(request, cached, *, now, max_age_seconds):
    """Fail closed on wrong identity, missing provenance or future/stale data.

    The caller supplies timestamps; this does not authenticate their source.
    """
    if not isinstance(request, dict) or not isinstance(cached, dict):
        raise ValueError("invalid_cache_record")
    if type(max_age_seconds) not in (int, float) or not 0 <= max_age_seconds <= 86400:
        raise ValueError("invalid_max_age")
    if any(not isinstance(request.get(k), str) or not request[k].strip()
           for k in REQUIRED_IDENTITY):
        raise ValueError("invalid_request_identity")
    reasons = []
    for field in REQUIRED_IDENTITY:
        if cached.get(field) != request[field]:
            reasons.append("identity_mismatch_" + field)
    try:
        observed = _aware(cached.get("observed_at"))
        checked = _aware(now)
        age = (checked - observed).total_seconds()
        if age < 0:
            reasons.append("future_observation")
        elif age > max_age_seconds:
            reasons.append("stale_observation")
    except ValueError:
        age = None
        reasons.append("invalid_observation_time")
    return {
        "accepted": not reasons,
        "reasons": sorted(reasons),
        "age_seconds": age,
        "provider_authenticity_verified": False,
        "trade_ready": False,
    }
