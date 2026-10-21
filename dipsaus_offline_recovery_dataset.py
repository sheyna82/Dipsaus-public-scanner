"""Offline JSONL research dataset ingestion with strict, bounded validation.

No downloads, external dependencies, training, orders or live alerts.
The caller remains responsible for point-in-time and data license checks.
"""
import json
from pathlib import Path
from dipsaus_offline_recovery_pipeline import evaluate_recovery_research

MAX_BYTES = 5_000_000
MAX_RECORDS = 5000


def load_recovery_jsonl(path, *, max_records=MAX_RECORDS):
    if type(max_records) is not int or not 1 <= max_records <= MAX_RECORDS:
        return None
    try:
        source = Path(path)
        if not source.is_file() or source.stat().st_size > MAX_BYTES:
            return None
        observations = []
        with source.open("r", encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    continue
                if len(observations) >= max_records:
                    return None
                obj = json.loads(line, parse_constant=lambda x: (_ for _ in ()).throw(ValueError(x)))
                if not isinstance(obj, dict):
                    return None
                observations.append(obj)
        return observations if observations else None
    except (OSError, UnicodeError, ValueError, TypeError, OverflowError):
        return None


def evaluate_recovery_jsonl(path, *, minimum_resolved=20, horizon=10):
    observations = load_recovery_jsonl(path)
    if observations is None:
        return None
    result = evaluate_recovery_research(
        observations, minimum_resolved=minimum_resolved, horizon=horizon)
    if result is None:
        return None
    result["source_type"] = "caller_supplied_local_jsonl"
    result["source_verified"] = False
    result["historical_performance_validated"] = False
    return result
