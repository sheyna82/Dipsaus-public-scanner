import unittest
from dipsaus_offline_earnings_asof_gate import audit_earnings_asof

SIGNAL = "2025-06-12T20:00:00+00:00"
START = "2025-01-01T00:00:00+00:00"
END = "2025-12-31T00:00:00+00:00"


class EarningsAsOfGateTests(unittest.TestCase):
    def evaluate(self, records, **kwargs):
        return audit_earnings_asof(SIGNAL, records,
                                   coverage_start=START, coverage_end=END, **kwargs)

    def test_future_published_revision_is_excluded(self):
        records = [
            {"issuer_id": "ABC", "published_at": "2025-06-11T12:00:00Z",
             "scheduled_event_at": "2025-06-20T12:00:00Z"},
            {"issuer_id": "ABC", "published_at": "2025-06-13T12:00:00Z",
             "scheduled_event_at": "2025-06-21T12:00:00Z"},
        ]
        result = self.evaluate(records)
        self.assertEqual(result["excluded_future_publications"], 1)
        self.assertEqual(len(result["visible_upcoming_events"]), 1)
        self.assertEqual(result["visible_upcoming_events"][0]["scheduled_event_at"],
                         "2025-06-20T12:00:00+00:00")

    def test_no_coverage_blocks_even_with_event(self):
        result = audit_earnings_asof(SIGNAL, [], coverage_start=None, coverage_end=END)
        self.assertEqual(result["status"], "DATA_BLOCKED")

    def test_naive_timestamps_block(self):
        result = self.evaluate([{"issuer_id": "ABC", "published_at": "2025-06-11",
                                 "scheduled_event_at": "2025-06-20"}])
        self.assertEqual(result["status"], "DATA_BLOCKED")

    def test_empty_attested_calendar_does_not_claim_completeness(self):
        result = self.evaluate([])
        self.assertEqual(result["status"], "ASOF_ATTESTATION_ONLY")
        self.assertFalse(result["calendar_completeness_verified"])
        self.assertFalse(result["trade_ready"])


if __name__ == "__main__":
    unittest.main()
