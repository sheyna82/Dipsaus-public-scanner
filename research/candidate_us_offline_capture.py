"""Offline-only US discovery evidence pipeline.

Consumes an explicitly supplied pre-outcome capture; never fetches market data,
runs the live scanner, or establishes independent timestamp provenance.
"""
import json
from pathlib import Path
from research.candidate_us_decision_record import decision_record
from research.candidate_us_decision_archive import archive_decision_batch


def build_records(capture):
    if not isinstance(capture, dict):
        raise ValueError("INVALID_CAPTURE")
    symbols = capture.get("sample_symbols")
    assessments = capture.get("assessments")
    failures = capture.get("failures")
    observed = capture.get("observed_at_utc")
    if not isinstance(symbols, list) or not symbols or any(not isinstance(s, str) or not s for s in symbols):
        raise ValueError("INVALID_SAMPLE")
    if len(symbols) != len(set(symbols)):
        raise ValueError("DUPLICATE_SAMPLE")
    if not isinstance(assessments, dict) or not isinstance(failures, dict):
        raise ValueError("INVALID_RESULTS")
    if not all(isinstance(s, str) for s in [*assessments, *failures]):
        raise ValueError("INVALID_SYMBOL_KEYS")
    if set(assessments) & set(failures):
        raise ValueError("CONFLICTING_OUTCOMES")
    if set(assessments) | set(failures) != set(symbols):
        raise ValueError("INCOMPLETE_OR_FOREIGN_SYMBOLS")
    records = [decision_record(s, assessments[s], observed) for s in sorted(assessments)]
    return {"records": records, "failed_symbols": dict(sorted(failures.items())),
            "requested_count": len(symbols), "assessed_count": len(records),
            "failure_count": len(failures), "prospective_capture_independently_verified": False}


def archive_capture(capture, archive_dir):
    result = build_records(capture)
    archive = archive_decision_batch(result["records"], capture["observed_at_utc"], archive_dir,
                                     failures=result["failed_symbols"], requested_count=result["requested_count"])
    return {**result, "archive": {"path": str(archive["path"]), "sha256": archive["sha256"]}}


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--capture", type=Path, required=True)
    parser.add_argument("--archive-dir", type=Path, default=Path("reports/candidate_entry_snapshots"))
    args = parser.parse_args()
    capture = json.loads(args.capture.read_text(encoding="utf-8"))
    print(json.dumps(archive_capture(capture, args.archive_dir), sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
