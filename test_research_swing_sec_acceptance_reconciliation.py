"""SEC acceptance-time reconciliation regression tests."""
import unittest
from research_swing_sec_acceptance_reconciliation import reconcile_sec_acceptance

URL = "https://www.sec.gov/Archives/edgar/data/example"
def candidate(raw):
    return {"accession": "0000320193-26-000001", "acceptance_raw": raw}
def reconcile(raw, documented="2026-10-26T21:03:00Z", **kwargs):
    return reconcile_sec_acceptance(candidate(raw),
        verified_document_timestamp=documented,
        verified_document_url=URL, **kwargs)

class SECReconciliationTests(unittest.TestCase):
    def test_matching_offset(self):
        result = reconcile("2026-10-26T17:03:00-04:00")
        self.assertTrue(result["acceptance_timestamp_verified"])
        self.assertFalse(result["release_timestamp_verified"])
        self.assertEqual(result["discrepancy_seconds"], 0)
    def test_timezone_naive_is_not_guessed(self):
        result = reconcile("2026-10-26T17:03:00")
        self.assertFalse(result["raw_timestamp_comparable"])
        self.assertFalse(result["release_timestamp_verified"])
    def test_conflicting_offset_rejected(self):
        with self.assertRaisesRegex(ValueError, "conflicting_acceptance_timestamps"):
            reconcile("2026-10-26T17:03:00Z")
    def test_missing_verification_url_rejected(self):
        with self.assertRaisesRegex(ValueError, "missing_verification_source"):
            reconcile_sec_acceptance(candidate("2026-10-26T17:03:00Z"),
                verified_document_timestamp="2026-10-26T21:03:00Z",
                verified_document_url="")
    def test_naive_document_timestamp_rejected(self):
        with self.assertRaisesRegex(ValueError, "timezone_required"):
            reconcile("2026-10-26T17:03:00-04:00",
                      documented="2026-10-26T21:03:00")
    def test_tolerance_enforced(self):
        with self.assertRaisesRegex(ValueError, "conflicting_acceptance_timestamps"):
            reconcile("2026-10-26T17:03:00-04:00",
                      documented="2026-10-26T21:04:01Z")

if __name__ == "__main__":
    unittest.main()
