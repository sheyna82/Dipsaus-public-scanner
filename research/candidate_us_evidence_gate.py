"""Research-only combined US batch evidence gate.

Validates archived decisions and independently supplied source chronology.
This cannot authenticate the supplied metadata or prove prospective capture.
"""
import json
from pathlib import Path
from research.candidate_us_decision_archive import verify_decision_archive
from research.candidate_us_provenance_audit import audit_capture_provenance


def audit_us_batch_evidence(archive_path, capture, source_records, expected_sha256=None):
    archive = verify_decision_archive(archive_path, expected_sha256)
    provenance = audit_capture_provenance(capture, source_records)
    payload = json.loads(Path(archive_path).read_text(encoding="utf-8"))
    if {r["symbol"] for r in payload["records"]} != set(capture.get("assessments", {})):
        raise ValueError("ARCHIVE_CAPTURE_SYMBOL_MISMATCH")
    if payload["failed_symbols"] != capture.get("failures", {}):
        raise ValueError("ARCHIVE_CAPTURE_FAILURE_DETAILS_MISMATCH")
    if archive["requested_count"] != len(capture["sample_symbols"]):
        raise ValueError("ARCHIVE_CAPTURE_COUNT_MISMATCH")
    if archive["record_count"] != len(capture.get("assessments", {})):
        raise ValueError("ARCHIVE_CAPTURE_ASSESSMENT_MISMATCH")
    if archive["failure_count"] != len(capture.get("failures", {})):
        raise ValueError("ARCHIVE_CAPTURE_FAILURE_MISMATCH")
    accepted = archive["screening_complete"] and provenance["metadata_chronology_accepted"]
    return {"research_only": True, "trade_ready": False, "evidence_gate_accepted": accepted,
            "independent_prospective_proof": False,
            "reasons": (["INCOMPLETE_SCREENING"] if not archive["screening_complete"] else []) +
                       (["INVALID_PROVENANCE_CHRONOLOGY"] if not provenance["metadata_chronology_accepted"] else []),
            "archive": archive, "provenance": provenance}
