"""Tests for SEC filing candidate normalization and fail-closed timing."""
import unittest
from research_swing_sec_submissions import (
    sec_submissions_endpoint, normalize_sec_recent_filings)

def payload(accepted="2026-10-26T17:03:00-04:00"):
    return {"cik": 320193, "filings": {"recent": {
        "accessionNumber": ["0000320193-26-000001"],
        "form": ["8-K"], "filingDate": ["2026-10-26"],
        "acceptanceDateTime": [accepted], "primaryDocument": ["report.htm"]}}}

class SECSubmissionTests(unittest.TestCase):
    def test_endpoint_padding(self):
        self.assertEqual(sec_submissions_endpoint(320193),
                         "https://data.sec.gov/submissions/CIK0000320193.json")
    def test_candidate_is_not_verified_event(self):
        result = normalize_sec_recent_filings(payload())[0]
        self.assertFalse(result["research_eligible"])
        self.assertFalse(result["release_timestamp_verified"])
        self.assertIsNone(result["first_observed_at"])
        self.assertFalse(result["acceptance_timestamp_verified"])
        self.assertEqual(result["acceptance_raw"], "2026-10-26T17:03:00-04:00")
        self.assertNotIn("acceptance_at_utc", result)
        self.assertIn("Archives/edgar/data/320193/", result["filing_url"])
    def test_naive_timestamp_rejected(self):
        with self.assertRaisesRegex(ValueError, "unverified_acceptance_timezone"):
            normalize_sec_recent_filings(payload("2026-10-26T17:03:00"))
    def test_parallel_column_mismatch_rejected(self):
        data = payload()
        data["filings"]["recent"]["form"] = []
        with self.assertRaisesRegex(ValueError, "misaligned_filing_columns"):
            normalize_sec_recent_filings(data)
    def test_irrelevant_forms_ignored(self):
        data = payload()
        data["filings"]["recent"]["form"] = ["4"]
        self.assertEqual(normalize_sec_recent_filings(data), [])
    def test_bad_cik_rejected(self):
        with self.assertRaisesRegex(ValueError, "invalid_cik"):
            sec_submissions_endpoint(0)

if __name__ == "__main__":
    unittest.main()
