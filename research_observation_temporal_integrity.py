"""Conservative timing audit for observations registered after a signal session.

A registration on or after the signal session is not automatically prospective.
No exchange calendar, market-close proof or independent timestamp is inferred.
"""
from datetime import date, datetime, timezone


def audit_observation_timing(record):
    if not isinstance(record, dict):
        raise ValueError("invalid_record")
    try:
        signal_day = date.fromisoformat(record["signal_session"])
        registered = datetime.fromisoformat(record["registered_at_utc"].replace("Z", "+00:00"))
        observed = datetime.fromisoformat(record["source_observed_at_utc"].replace("Z", "+00:00"))
    except (KeyError, TypeError, ValueError, AttributeError) as exc:
        raise ValueError("invalid_timing_fields") from exc
    if registered.tzinfo is None or registered.utcoffset() != timezone.utc.utcoffset(registered):
        raise ValueError("registration_time_not_utc")
    if observed.tzinfo is None or observed.utcoffset() != timezone.utc.utcoffset(observed):
        raise ValueError("observation_time_not_utc")
    if observed > registered:
        raise ValueError("observation_after_registration")
    if record.get("research_only") is not True or record.get("trade_ready") is not False:
        raise ValueError("unsafe_record")
    if record.get("future_outcome") is not None:
        raise ValueError("future_outcome_present")
    if record.get("registration_clock_proof_independent") is not False:
        raise ValueError("unsupported_registration_clock_proof")
    if record.get("independent_source_authentication") is not False:
        raise ValueError("unsupported_source_proof")
    if registered.date() > signal_day:
        classification = "late_registration_not_prospective_for_signal_session"
    else:
        classification = "same_day_registration_requires_exchange_cutoff_proof"
    return {
        "status": classification,
        "signal_session": signal_day.isoformat(),
        "registered_at_utc_claimed": registered.isoformat(),
        "independent_pre_signal_timestamp_proof": False,
        "prospective_signal_proven": False,
        "research_only": True,
        "trade_ready": False,
    }
