"""Research-only coordinated gate for historical data eligibility.

A pass checks supplied metadata, not the truth of external market records.
"""

from research_asof_revision_selector import select_asof_revision
from research_point_in_time_availability_gate import assess_point_in_time_record


def assess_historical_revision(versions, *, decision_at):
    """Select an as-of revision and require point-in-time metadata to pass."""
    # Audit every candidate first: an invalid latest revision must not hide a
    # valid earlier version, nor be silently selected as a valid snapshot.
    eligible_records = []
    rejected = []
    for version in versions:
        audit = assess_point_in_time_record(version, decision_at=decision_at)
        if audit["accepted"]:
            eligible_records.append(version)
        else:
            rejected.extend(audit["reasons"])
    selection = select_asof_revision(eligible_records, decision_at=decision_at) if eligible_records else None
    if selection is None:
        return {
            "accepted": False, "revision_id": None,
            "reasons": sorted(set(rejected)) or ["no_version_available_asof"],
            "source_authenticity_verified": False, "trade_ready": False,
        }
    if not selection["accepted"]:
        return {
            "accepted": False, "revision_id": None,
            "reasons": [selection["reason"]],
            "source_authenticity_verified": False, "trade_ready": False,
        }
    selected = next(v for v in versions if v["revision_id"] == selection["revision_id"])
    audit = assess_point_in_time_record(selected, decision_at=decision_at)
    return {
        "accepted": audit["accepted"],
        "revision_id": selection["revision_id"] if audit["accepted"] else None,
        "reasons": audit["reasons"],
        "source_authenticity_verified": False,
        "trade_ready": False,
    }
