"""Offline event snapshot acceptance regression."""
import unittest
from research_event_snapshot_gate import audit_event_snapshot


def sample(**changes):
    args = dict(symbol="AMD", event_date="2026-11-03",
                captured_at_utc="2026-10-24T12:00:00Z",
                close_price="100.50", benchmark_close="200.25",
                source="synthetic_fixture", as_of_date="2026-10-24")
    args.update(changes)
    return audit_event_snapshot(**args)


class EventSnapshotGateTests(unittest.TestCase):
    def test_valid_synthetic_snapshot_is_not_verified_source(self):
        result = sample()
        self.assertTrue(result["snapshot_temporally_valid"])
        self.assertFalse(result["source_authenticity_verified"])
        self.assertFalse(result["issuer_event_time_verified"])
        self.assertFalse(result["trade_ready"])
        self.assertFalse(result["prediction_issued"])

    def test_no_hindsight_or_future_snapshot(self):
        for changes, error in (
            ({"captured_at_utc": "2026-11-03T01:00:00Z",
              "as_of_date": "2026-11-04"}, "snapshot_not_strictly_before_event_date"),
            ({"captured_at_utc": "2026-10-25T01:00:00Z"},
             "snapshot_after_as_of_date"),
            ({"captured_at_utc": "2026-10-24T01:00:00"},
             "snapshot_timestamp_requires_timezone"),
        ):
            with self.subTest(changes=changes):
                with self.assertRaisesRegex(ValueError, error):
                    sample(**changes)

    def test_reject_invalid_price_or_source(self):
        for value in ("0", "-1", "NaN", "Infinity", "abc"):
            with self.subTest(value=value):
                with self.assertRaisesRegex(ValueError, "invalid_snapshot_price"):
                    sample(close_price=value)
        with self.assertRaisesRegex(ValueError, "missing_snapshot_source"):
            sample(source=" ")

    def test_event_symbol_and_date_must_match_frozen_cohort(self):
        with self.assertRaisesRegex(ValueError, "unknown_or_mismatched_event"):
            sample(event_date="2026-11-02")


if __name__ == "__main__":
    unittest.main()
