"""Offline provenance chronology tests; no network or live scanner."""
import unittest
from research.candidate_us_provenance_audit import audit_capture_provenance


def source():
    return {"provider": "example", "observed_at": "2026-11-02T20:00:00Z",
            "published_at": "2026-11-02T21:00:00Z",
            "ingested_at": "2026-11-02T21:05:00Z",
            "revision_asof": "2026-11-02T21:00:00Z"}


class CaptureProvenanceTests(unittest.TestCase):
    def setUp(self):
        self.capture = {"sample_symbols": ["AAA"], "observed_at_utc": "2026-11-03T12:00:00Z"}

    def test_valid_chronology_does_not_claim_independent_proof(self):
        result = audit_capture_provenance(self.capture, {"AAA": source()})
        self.assertTrue(result["metadata_chronology_accepted"])
        self.assertFalse(result["independent_prospective_proof"])
        self.assertFalse(result["trade_ready"])

    def test_future_publication_is_blocked(self):
        item = source()
        item["published_at"] = "2026-11-04T12:00:00Z"
        result = audit_capture_provenance(self.capture, {"AAA": item})
        self.assertFalse(result["metadata_chronology_accepted"])

    def test_missing_symbol_metadata_is_blocked(self):
        with self.assertRaisesRegex(ValueError, "PROVENANCE_COVERAGE_MISMATCH"):
            audit_capture_provenance(self.capture, {})


if __name__ == "__main__":
    unittest.main()
