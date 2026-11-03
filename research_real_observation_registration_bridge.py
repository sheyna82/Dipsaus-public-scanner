"""Research-only handoff from validated observation to immutable registration.

The source URL and local observation timestamp remain unverified assertions.
No live scanner integration, external fetching or trade authorization.
"""
from research_prospective_real_candidate_intake import validate_prospective_observation
from research_immutable_candidate_registration import register_candidate_once


def register_validated_observation(observation, directory, *, clock):
    checked = validate_prospective_observation(observation, now_utc=clock())
    # The immutable record contains the exact source assertions and the explicit
    # absence of independent provenance proof. Registration adds its own UTC time.
    candidate = dict(observation)
    candidate["source_schema_status"] = checked["status"]
    candidate["independent_source_authentication"] = False
    candidate["independent_timestamp_proof"] = False
    candidate["research_only"] = True
    candidate["trade_ready"] = False
    candidate["future_outcome"] = None
    registered = register_candidate_once(candidate, directory, clock=clock)
    return {
        **registered,
        "source_schema_accepted": True,
        "independent_market_data_provenance": False,
        "independent_pre_signal_timestamp_proof": False,
        "trade_ready": False,
    }
