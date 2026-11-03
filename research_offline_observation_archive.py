"""Research-only offline intake: supplied bytes -> immutable candidate -> ZIP.

No source fetch or independently trusted timestamp. A caller must supply an
observation; this function never infers a trading signal from source bytes.
"""
from pathlib import Path

from research_offline_source_evidence import prepare_offline_source_evidence
from research_source_secret_screen import reject_obvious_secrets
from research_source_bound_registration import register_observation_with_source_snapshot
from research_source_evidence_archive import archive_source_evidence


def archive_offline_observation(observation, source_bytes, candidate_directory,
                                archive_path, *, clock, allowed_hosts):
    if not isinstance(observation, dict):
        raise ValueError("invalid_observation")
    # Fail closed before registration: reject conflicting source metadata.
    if observation.get("source_url") is None:
        raise ValueError("missing_source_url")
    if observation.get("source_observed_at_utc") is None:
        raise ValueError("missing_source_observed_at_utc")
    reject_obvious_secrets(source_bytes)
    now = clock()
    evidence = prepare_offline_source_evidence(
        observation["source_url"], source_bytes=source_bytes,
        captured_at_utc=now, allowed_hosts=allowed_hosts)
    if Path(archive_path).exists():
        raise FileExistsError("source_archive_already_exists")
    if observation.get("offline_supplied_bytes") not in (None, True):
        raise ValueError("conflicting_offline_evidence_flag")
    candidate = dict(observation)
    candidate["offline_supplied_bytes"] = True
    candidate["source_bytes_independently_authenticated"] = False
    registered = register_observation_with_source_snapshot(
        candidate, source_bytes, candidate_directory, clock=lambda: now)
    verified = archive_source_evidence(registered["path"], source_bytes, archive_path)
    return {
        "registration": registered,
        "archive_verification": verified,
        "source_sha256": evidence["source_sha256"],
        "independent_source_authentication": False,
        "independent_timestamp_proof": False,
        "trade_ready": False,
    }
