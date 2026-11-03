"""Offline freshness audit for preserved Finnhub quotes, not independent quote validation."""
import json
from datetime import datetime, timezone
from pathlib import Path
from research_verify_finnhub_observation import verify

def audit_preserved_quote_freshness(paths, *, maximum_claimed_lag_seconds=120):
    if not isinstance(paths,(list,tuple)) or not paths:
        raise ValueError("observation_paths_required")
    if type(maximum_claimed_lag_seconds) is not int or not 1 <= maximum_claimed_lag_seconds <= 3600:
        raise ValueError("invalid_lag_threshold")
    observations=[]
    for path in paths:
        checked=verify(path)
        record=json.loads(Path(path).read_text(encoding="utf-8"))
        raw=json.loads(bytes.fromhex(record["raw_response_hex"]))
        timestamp=raw.get("t")
        if type(timestamp) is not int or timestamp <= 0:
            raise ValueError("invalid_provider_timestamp")
        captured=datetime.fromisoformat(record["response_finished_utc"])
        claimed=datetime.fromtimestamp(timestamp,timezone.utc)
        lag=(captured-claimed).total_seconds()
        if lag < 0:
            raise ValueError("provider_timestamp_after_capture")
        observations.append({
            "symbol":checked["symbol"],
            "provider_timestamp_claimed_utc":claimed.isoformat(),
            "capture_finished_utc":captured.isoformat(),
            "claimed_lag_seconds":round(lag,6),
            "within_lag_threshold":lag <= maximum_claimed_lag_seconds,
            "independent_timestamp_proof":False,
            "quote_accuracy_verified":False,
            "trade_ready":False,
        })
    observations.sort(key=lambda o:(o["capture_finished_utc"],o["symbol"]))
    return {"schema":"dipsaus_research_claimed_quote_freshness_v1",
            "observation_count":len(observations),
            "all_within_claimed_lag_threshold":all(o["within_lag_threshold"] for o in observations),
            "maximum_claimed_lag_seconds":maximum_claimed_lag_seconds,
            "observations":observations,
            "independent_timestamp_proof":False,
            "trade_ready":False}
