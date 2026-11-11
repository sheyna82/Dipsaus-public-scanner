"""Research-only boundary gate for candidate registration and future outcomes.

A historical signal session is never itself evidence of when a candidate was recorded.
"""
from datetime import datetime
from zoneinfo import ZoneInfo


def audit_capture_candidate_boundary(manifest, *, registered_at_utc, outcome_sessions=()):
    if manifest.get("prospective_candidate_registered") is not False:
        raise ValueError("capture_manifest_not_pre_registration")
    if manifest.get("independent_prospective_proof") is not False:
        raise ValueError("unsupported_prospective_proof_claim")
    captured = datetime.fromisoformat(manifest["captured_at_utc"])
    registered = datetime.fromisoformat(registered_at_utc)
    if any(d.tzinfo is None or d.utcoffset() is None for d in (captured, registered)):
        raise ValueError("timezone_required")
    if registered < captured:
        raise ValueError("candidate_registered_before_source_capture")
    # Daily bars dated on the registration date can contain pre-registration
    # trading; conservatively allow outcomes only on subsequent NY dates.
    registration_day = registered.astimezone(ZoneInfo("America/New_York")).date().isoformat()
    if any(day <= registration_day for day in outcome_sessions):
        raise ValueError("outcome_session_not_after_registration")
    if any(day <= manifest["last_common_eligible_session"] for day in outcome_sessions):
        raise ValueError("outcome_overlaps_input")
    return {"research_only": True, "trade_ready": False,
            "capture_precedes_registration": True,
            "registration_at_utc": registered.isoformat(),
            "earliest_permitted_outcome_session_exclusive": registration_day,
            "source_authenticated_independently": False,
            "independent_prospective_proof": False}
