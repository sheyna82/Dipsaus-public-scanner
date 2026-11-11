"""Conservative evidence-readiness assessment for offline Finnhub collections.

An observation archive is not a candidate registration or a trading signal.
No market access, orders, or provider-authentication claims are made.
"""
from datetime import datetime

def assess_observation_coverage(collection, *, minimum_distinct_days=5,
                                minimum_observations=20):
    if not isinstance(collection, dict) or collection.get("schema") != "dipsaus_research_artifact_collection_v1":
        raise ValueError("invalid_collection_schema")
    observations = collection.get("observations")
    if not isinstance(observations, list) or collection.get("count") != len(observations):
        raise ValueError("invalid_collection_count")
    if type(minimum_distinct_days) is not int or minimum_distinct_days < 2:
        raise ValueError("invalid_day_threshold")
    if type(minimum_observations) is not int or minimum_observations < 2:
        raise ValueError("invalid_observation_threshold")
    if any(collection.get(flag) is not False for flag in
           ("quote_accuracy_verified", "prospective_signal_proven", "trade_ready")):
        raise ValueError("unsafe_collection_claim")
    days = set()
    symbols = set()
    for observation in observations:
        if not isinstance(observation, dict) or observation.get("trade_ready") is not False:
            raise ValueError("unsafe_observation")
        try:
            timestamp = datetime.fromisoformat(observation["request_started_utc"])
            if timestamp.tzinfo is None or timestamp.utcoffset().total_seconds() != 0:
                raise ValueError("invalid_timestamp")
            symbol = observation["symbol"]
            if symbol not in {"AMD", "COHU", "CSGP", "AAPL"}:
                raise ValueError("invalid_symbol")
        except (KeyError, TypeError, AttributeError) as exc:
            raise ValueError("invalid_observation") from exc
        days.add(timestamp.date().isoformat())
        symbols.add(symbol)
    reasons = []
    if len(observations) < minimum_observations:
        reasons.append("INSUFFICIENT_OBSERVATIONS")
    if len(days) < minimum_distinct_days:
        reasons.append("INSUFFICIENT_DISTINCT_DAYS")
    reasons.extend(("PROVIDER_NOT_INDEPENDENTLY_AUTHENTICATED",
                    "NO_PROSPECTIVE_CANDIDATE_OUTCOMES"))
    return {"schema":"dipsaus_research_observation_coverage_v1",
            "observation_count":len(observations),
            "distinct_utc_days":len(days), "distinct_symbols":len(symbols),
            "minimum_observations":minimum_observations,
            "minimum_distinct_days":minimum_distinct_days,
            "coverage_thresholds_met":len(observations)>=minimum_observations and len(days)>=minimum_distinct_days,
            "trade_ready":False, "prospective_edge_proven":False,
            "blocking_reasons":reasons}
