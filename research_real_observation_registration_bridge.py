"""Research-only handoff from validated observation to immutable registration.

The source URL and local observation timestamp remain unverified assertions.
No live scanner integration, external fetching or trade authorization.
"""
from research_prospective_real_candidate_intake import validate_prospective_observation
from research_immutable_candidate_registration import register_candidate_once
from research_observation_temporal_integrity import audit_observation_timing
import json
from pathlib import Path


def register_validated_observation(observation, directory, *, clock):
    captured_at = clock()
    checked = validate_prospective_observation(observation, now_utc=captured_at)
    # The immutable record contains the exact source assertions and the explicit
    # absence of independent provenance proof. Registration adds its own UTC time.
    candidate = dict(observation)
    candidate["source_schema_status"] = checked["status"]
    candidate["independent_source_authentication"] = False
    candidate["independent_timestamp_proof"] = False
    candidate["research_only"] = True
    candidate["trade_ready"] = False
    candidate["future_outcome"] = None
    registered = register_candidate_once(candidate, directory, clock=lambda: captured_at)
    stored_record = json.loads(Path(registered["path"]).read_text(encoding="utf-8"))
    timing = audit_observation_timing(stored_record)
    return {
        **registered,
        "temporal_integrity": timing,
        "source_schema_accepted": True,
        "independent_market_data_provenance": False,
        "independent_pre_signal_timestamp_proof": False,
        "trade_ready": False,
    }
