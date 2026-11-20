import unittest
from research_historical_event_contract import validate_historical_events as validate

SIGNAL = dict(schema_version=1, event_id="s1", candidate_id="opaque1",
              observed_utc="2026-01-01T12:00:00Z", event_type="SIGNAL",
              source_digest="source-digest", decision="REJECTED",
              feature_digest="a" * 64)
OUTCOME = dict(schema_version=1, event_id="o1", candidate_id="opaque1",
               observed_utc="2026-01-10T12:00:00Z", event_type="OUTCOME",
               source_digest="outcome-source", return_pct=-2.5,
               horizon_sessions=5)

class HistoricalEventContractTests(unittest.TestCase):
    def test_rejected_signal_with_outcome(self):
        r = validate([SIGNAL, OUTCOME])
        self.assertEqual(r["signal_count"], 1)
        self.assertEqual(r["outcome_count"], 1)
        self.assertFalse(r["trade_ready"])

    def test_missing_outcome_is_visible(self):
        r = validate([SIGNAL])
        self.assertEqual(r["missing_outcome_count"], 1)
        self.assertFalse(r["archive_completeness_verified"])

    def test_ticker_leak_blocked(self):
        self.assertEqual(validate([{**SIGNAL, "ticker": "PRIVATE"}])["status"],
                         "EVENT_CONTRACT_BLOCKED")

    def test_unknown_field_blocked(self):
        self.assertEqual(validate([{**SIGNAL, "payload": "raw"}])["status"],
                         "EVENT_CONTRACT_BLOCKED")

    def test_outcome_before_signal_blocked(self):
        self.assertEqual(validate([SIGNAL, {**OUTCOME, "observed_utc": "2025-12-01T12:00:00Z"}])["reason"],
                         "ORPHAN_OR_NONFUTURE_OUTCOME")

    def test_orphan_outcome_blocked(self):
        self.assertEqual(validate([OUTCOME])["reason"], "ORPHAN_OR_NONFUTURE_OUTCOME")

    def test_duplicate_event_blocked(self):
        self.assertEqual(validate([SIGNAL, SIGNAL])["reason"], "DUPLICATE_EVENT")

    def test_nonfinite_outcome_blocked(self):
        self.assertEqual(validate([SIGNAL, {**OUTCOME, "return_pct": float("nan")}])["reason"],
                         "DUPLICATE_OR_INVALID_OUTCOME")

    def test_invalid_digest_blocked(self):
        self.assertEqual(validate([{**SIGNAL, "feature_digest": "unverified"}])["reason"],
                         "INVALID_FEATURE_DIGEST")

    def test_naive_timestamp_blocked(self):
        self.assertEqual(validate([{**SIGNAL, "observed_utc": "2026-01-01"}])["reason"],
                         "INVALID_TIMESTAMP")

if __name__ == "__main__":
    unittest.main()
