import unittest
from research_historical_coverage import audit_historical_coverage as audit

SIGNALS = [
    dict(id="a", decision="SELECTED", observed_utc="2026-01-01T00:00:00Z"),
    dict(id="b", decision="REJECTED", observed_utc="2026-01-01T00:00:00Z"),
]
OUTCOME = dict(id="a", observed_utc="2026-01-10T00:00:00Z", return_pct=3.0)

class HistoricalCoverageTests(unittest.TestCase):
    def test_missing_rejected_outcome_visible(self):
        r = audit(SIGNALS, [OUTCOME])
        self.assertEqual(r["missing_outcome_ids"], ["b"])
        self.assertEqual(r["outcome_coverage_fraction"], .5)
        self.assertEqual(r["decision_counts"]["REJECTED"], 1)
        self.assertFalse(r["complete_candidate_universe_verified"])

    def test_orphan_outcome_blocks(self):
        self.assertEqual(audit(SIGNALS, [{**OUTCOME, "id": "z"}])["reason"], "ORPHAN_OUTCOME")

    def test_duplicate_signal_blocks(self):
        self.assertEqual(audit([SIGNALS[0], SIGNALS[0]], [])["reason"], "DUPLICATE_SIGNAL")

    def test_duplicate_outcome_blocks(self):
        self.assertEqual(audit(SIGNALS, [OUTCOME, OUTCOME])["reason"], "DUPLICATE_OUTCOME")

    def test_outcome_before_signal_blocks(self):
        self.assertEqual(audit(SIGNALS, [{**OUTCOME, "observed_utc": "2025-12-01T00:00:00Z"}])["reason"],
                         "INVALID_OUTCOME_TIME")

    def test_naive_timestamp_blocks(self):
        self.assertEqual(audit([{**SIGNALS[0], "observed_utc": "2026-01-01"}], [])["reason"],
                         "INVALID_SIGNAL_TIME")

    def test_unknown_decision_blocks(self):
        self.assertEqual(audit([{**SIGNALS[0], "decision": "WINNER"}], [])["reason"],
                         "INVALID_DECISION")

    def test_missing_return_blocks(self):
        r = audit(SIGNALS, [{**OUTCOME, "return_pct": None}])
        self.assertEqual(r["reason"], "INVALID_OUTCOME_VALUE")

    def test_nonfinite_return_blocks(self):
        r = audit(SIGNALS, [{**OUTCOME, "return_pct": float("inf")}])
        self.assertEqual(r["reason"], "INVALID_OUTCOME_VALUE")

    def test_empty_collection_is_not_complete_proof(self):
        r = audit([], [])
        self.assertIsNone(r["outcome_coverage_fraction"])
        self.assertFalse(r["complete_candidate_universe_verified"])

if __name__ == "__main__":
    unittest.main()
