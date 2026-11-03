"""Research-only create-only archive of independently supplied US decision records.

Does not call the live scanner or establish independent capture timestamps.
"""
import hashlib
import json
from pathlib import Path
from research.candidate_entry_snapshot import archive_candidate_snapshot


def archive_decision_batch(records, generated_utc, archive_dir=Path("reports/candidate_entry_snapshots"), *, failures=None, requested_count=None):
    if not isinstance(records, list):
        raise ValueError("INVALID_DECISION_BATCH")
    if failures is None:
        failures = {}
    if not isinstance(failures, dict) or any(not isinstance(k, str) or not k or not isinstance(v, str) or not v for k, v in failures.items()):
        raise ValueError("INVALID_FAILURE_RECORDS")
    if not records and not failures:
        raise ValueError("EMPTY_DECISION_BATCH")
    if not all(isinstance(r, dict) and r.get("research_only") is True and
               r.get("trade_ready") is False and isinstance(r.get("sha256"), str)
               for r in records):
        raise ValueError("UNVERIFIED_DECISION_RECORD")
    for record in records:
        body = {k: v for k, v in record.items() if k != "sha256"}
        canonical = json.dumps(body, sort_keys=True, separators=(",", ":"), allow_nan=False)
        if hashlib.sha256(canonical.encode("utf-8")).hexdigest() != record["sha256"]:
            raise ValueError("DECISION_RECORD_HASH_MISMATCH")
    symbols = [r.get("symbol") for r in records]
    if any(not isinstance(s, str) or not s for s in symbols) or len(set(symbols)) != len(symbols):
        raise ValueError("INVALID_OR_DUPLICATE_SYMBOLS")
    if set(symbols) & set(failures):
        raise ValueError("CONFLICTING_ARCHIVE_OUTCOMES")
    if requested_count is None:
        requested_count = len(records) + len(failures)
    if type(requested_count) is not int or requested_count != len(records) + len(failures):
        raise ValueError("ARCHIVE_COVERAGE_MISMATCH")
    if not isinstance(generated_utc, str) or not generated_utc.endswith(("+00:00", "Z")):
        raise ValueError("INVALID_GENERATED_TIME")
    payload = {
        "generated_utc": generated_utc,
        "research_only": True,
        "trade_ready": False,
        "prospective_capture_independently_verified": False,
        "record_count": len(records),
        "requested_count": requested_count,
        "failure_count": len(failures),
        "failed_symbols": dict(sorted(failures.items())),
        "screening_complete": not bool(failures),
        "records": sorted(records, key=lambda r: r["symbol"]),
    }
    return archive_candidate_snapshot(payload, Path(archive_dir))
