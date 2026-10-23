"""Research-only selection of historical data revisions available at decision time.

Timestamps are caller supplied; provenance and snapshot authenticity are unverified.
"""

from datetime import datetime


def _aware(value):
    if not isinstance(value, str):
        raise ValueError("invalid_timestamp")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError("invalid_timestamp") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("timezone_required")
    return parsed


def select_asof_revision(versions, *, decision_at):
    """Select latest revision both published and ingested by decision time.

    Each version requires revision_id, published_at and ingested_at.
    Reject ambiguous duplicate identifiers and conflicting revision timestamps.
    """
    decision = _aware(decision_at)
    if not isinstance(versions, (list, tuple)) or not versions:
        raise ValueError("invalid_versions")
    seen = set()
    eligible = []
    for version in versions:
        if not isinstance(version, dict):
            raise ValueError("invalid_version")
        identifier = version.get("revision_id")
        if not isinstance(identifier, str) or not identifier.strip() or identifier in seen:
            raise ValueError("invalid_or_duplicate_revision_id")
        seen.add(identifier)
        published = _aware(version.get("published_at"))
        ingested = _aware(version.get("ingested_at"))
        if ingested < published:
            raise ValueError("ingestion_before_publication")
        if published <= decision and ingested <= decision:
            eligible.append((published, ingested, identifier))
    if not eligible:
        return {
            "accepted": False, "revision_id": None,
            "reason": "no_version_available_asof",
            "historical_snapshot_verified": False, "trade_ready": False,
        }
    eligible.sort()
    if len(eligible) > 1 and eligible[-1][:2] == eligible[-2][:2]:
        raise ValueError("ambiguous_revision_order")
    return {
        "accepted": True, "revision_id": eligible[-1][2],
        "reason": None,
        "historical_snapshot_verified": False, "trade_ready": False,
    }
