"""Research-only point-in-time availability audit; no external data verification."""

from datetime import datetime


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


def assess_point_in_time_record(record, *, decision_at):
    """Fail closed when an observation or revision was not yet available.

    This checks supplied metadata, not the authenticity of its source.
    """
    if not isinstance(record, dict):
        raise ValueError("invalid_record")
    decision = _aware(decision_at)
    reasons = []
    required = ("observed_at", "published_at", "ingested_at", "revision_asof")
    timestamps = {}
    for key in required:
        try:
            timestamps[key] = _aware(record.get(key))
        except ValueError:
            reasons.append("invalid_" + key)
    if len(timestamps) == len(required):
        if timestamps["published_at"] < timestamps["observed_at"]:
            reasons.append("publication_before_observation")
        if timestamps["ingested_at"] < timestamps["published_at"]:
            reasons.append("ingestion_before_publication")
        if timestamps["revision_asof"] < timestamps["observed_at"]:
            reasons.append("revision_before_observation")
        for key in ("published_at", "ingested_at", "revision_asof"):
            if timestamps[key] > decision:
                reasons.append("future_" + key)
    return {
        "accepted": not reasons,
        "reasons": sorted(reasons),
        "source_authenticity_verified": False,
        "historical_snapshot_verified": False,
        "trade_ready": False,
    }
