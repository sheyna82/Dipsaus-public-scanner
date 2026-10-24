"""Synthetic event-release timing tests; no issuer times are asserted."""
import unittest
from research_event_release_timing import audit_event_release_timing


def run(**overrides):
    args = dict(event_date="2026-11-03",
                release_timestamp="2026-11-03T21:30:00Z",
                market_close_timestamp="2026-11-03T21:00:00Z",
                first_followup_close_timestamp="2026-11-04T21:00:00Z",
                source="synthetic_fixture")
    args.update(overrides)
    return audit_event_release_timing(**args)


class EventTimingTests(unittest.TestCase):
    def test_after_close_order_is_only_temporally_valid(self):
        result = run()
        self.assertTrue(result["temporal_order_verified"])
        self.assertFalse(result["issuer_release_source_authenticated"])
        self.assertFalse(result["event_window_trade_ready"])

    def test_reject_before_close_and_same_day_followup(self):
        for changes, expected in (
            ({"release_timestamp": "2026-11-03T20:00:00Z"},
             "not_after_market_close"),
            ({"first_followup_close_timestamp": "2026-11-03T21:10:00Z"},
             "followup_not_after_release"),
            ({"release_timestamp": "2026-11-04T01:00:00Z"},
             "release_date_mismatch"),
            ({"market_close_timestamp": "2026-11-02T21:00:00Z"},
             "market_close_event_date_mismatch"),
        ):
            with self.subTest(changes=changes):
                with self.assertRaisesRegex(ValueError, expected):
                    run(**changes)

    def test_reject_unzoned_timestamp_and_missing_source(self):
        with self.assertRaisesRegex(ValueError, "release_timezone_required"):
            run(release_timestamp="2026-11-03T21:30:00")
        with self.assertRaisesRegex(ValueError, "missing_release_source"):
            run(source="")


if __name__ == "__main__":
    unittest.main()
