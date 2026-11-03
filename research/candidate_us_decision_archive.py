"""Research-only create-only archive of independently supplied US decision records.

Does not call the live scanner or establish independent capture timestamps.
"""
from pathlib import Path
from research.candidate_entry_snapshot import archive_candidate_snapshot


def archive_decision_batch(records, generated_utc, archive_dir=Path("reports/candidate_entry_snapshots")):
    if not isinstance(records, list) or not records:
        raise ValueError("EMPTY_DECISION_BATCH")
    if not all(isinstance(r, dict) and r.get("research_only") is True and
               r.get("trade_ready") is False and isinstance(r.get("sha256"), str)
               for r in records):
        raise ValueError("UNVERIFIED_DECISION_RECORD")
    symbols = [r.get("symbol") for r in records]
    if any(not isinstance(s, str) or not s for s in symbols) or len(set(symbols)) != len(symbols):
        raise ValueError("INVALID_OR_DUPLICATE_SYMBOLS")
    if not isinstance(generated_utc, str) or not generated_utc.endswith(("+00:00", "Z")):
        raise ValueError("INVALID_GENERATED_TIME")
    payload = {
        "generated_utc": generated_utc,
        "research_only": True,
        "trade_ready": False,
        "prospective_capture_independently_verified": False,
        "record_count": len(records),
        "records": sorted(records, key=lambda r: r["symbol"]),
    }
    return archive_candidate_snapshot(payload, Path(archive_dir))
