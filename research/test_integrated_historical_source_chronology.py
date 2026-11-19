"""Synthetic chronology tests: caller timestamps never prove historical publication."""
import unittest
from integrated_historical_source_chronology import assess_historical_source_chronology

ENTRY = "2025-06-12T09:30:00-04:00"


class HistoricalSourceChronologyTests(unittest.TestCase):
    def test_post_entry_retrieval_cannot_prove_pre_entry_publication(self):
        result = assess_historical_source_chronology(
            ENTRY, "2025-07-01T12:00:00Z", "2025-06-11T14:00:00Z")
        self.assertFalse(result["retrieval_precedes_entry"])
        self.assertTrue(result["claimed_publication_precedes_entry"])
        self.assertFalse(result["historical_publication_independently_proven"])
        self.assertFalse(result["eligible_for_backtest_performance_claim"])

    def test_supplied_pre_entry_retrieval_is_still_unverified(self):
        result = assess_historical_source_chronology(
            ENTRY, "2025-06-11T20:00:00Z", "2025-06-11T19:00:00Z")
        self.assertTrue(result["retrieval_precedes_entry"])
        self.assertFalse(result["timestamp_claims_independently_authenticated"])
        self.assertFalse(result["trade_ready"])

    def test_missing_publication_timestamp_does_not_get_inferred(self):
        result = assess_historical_source_chronology(ENTRY, "2025-06-13T12:00:00Z")
        self.assertFalse(result["claimed_publication_precedes_entry"])

    def test_naive_and_impossible_timestamps_rejected(self):
        with self.assertRaisesRegex(ValueError, "NAIVE_EVIDENCE_TIMESTAMP"):
            assess_historical_source_chronology(ENTRY, "2025-06-11T12:00:00")
        with self.assertRaisesRegex(ValueError, "INVALID_EVIDENCE_TIMESTAMP"):
            assess_historical_source_chronology(ENTRY, "not a date")

    def test_publication_after_retrieval_rejected(self):
        with self.assertRaisesRegex(ValueError, "PUBLICATION_CLAIM_AFTER_RETRIEVAL"):
            assess_historical_source_chronology(
                ENTRY, "2025-06-11T12:00:00Z", "2025-06-12T12:00:00Z")

    def test_future_retrieval_rejected(self):
        with self.assertRaisesRegex(ValueError, "FUTURE_RETRIEVAL_TIMESTAMP"):
            assess_historical_source_chronology(ENTRY, "2099-01-01T00:00:00Z")


if __name__ == "__main__":
    unittest.main()
