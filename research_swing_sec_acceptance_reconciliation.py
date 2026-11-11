"""Independent SEC filing acceptance-time reconciliation (offline only).

Compare independently documented, timezone-aware filing acceptance timestamps.
A match verifies a filing acceptance time, NOT an earnings news release time.
"""
from datetime import timedelta
from research_swing_event_dataset_audit import _utc


def reconcile_sec_acceptance(candidate, *, verified_document_timestamp,
                             verified_document_url, max_disagreement_seconds=60):
    if not isinstance(candidate, dict) or not candidate.get("accession"):
        raise ValueError("invalid_candidate")
    if not isinstance(verified_document_url, str) or not verified_document_url.startswith("https://"):
        raise ValueError("missing_verification_source")
    if type(max_disagreement_seconds) not in (int, float) or not 0 <= max_disagreement_seconds <= 3600:
        raise ValueError("invalid_tolerance")
    documented = _utc(verified_document_timestamp)
    raw = candidate.get("acceptance_raw")
    if not isinstance(raw, str):
        raise ValueError("missing_raw_acceptance")
    # SEC submissions may omit a timezone. Never guess one.
    try:
        observed = _utc(raw)
    except ValueError:
        return {
            "accession": candidate["accession"], "accepted_at_utc": documented.isoformat(),
            "raw_timestamp_comparable": False, "acceptance_timestamp_verified": True,
            "verification_source_url": verified_document_url,
            "release_timestamp_verified": False, "trade_ready": False,
        }
    discrepancy = abs((observed - documented).total_seconds())
    if discrepancy > max_disagreement_seconds:
        raise ValueError("conflicting_acceptance_timestamps")
    return {
        "accession": candidate["accession"], "accepted_at_utc": documented.isoformat(),
        "raw_timestamp_comparable": True, "discrepancy_seconds": discrepancy,
        "acceptance_timestamp_verified": True,
        "verification_source_url": verified_document_url,
        "release_timestamp_verified": False, "trade_ready": False,
    }
