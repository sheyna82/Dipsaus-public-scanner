import unittest
from research_swing_verified_event_runner import run_verified_event_study

def payload():
    bars = []
    for day in range(1, 15):
        bars.append({"open_at": f"2026-10-{day:02d}T09:30:00Z",
                     "close_at": f"2026-10-{day:02d}T16:00:00Z",
                     "open": 100.0 + day, "high": 102.0 + day,
                     "low": 99.0 + day, "close": 101.0 + day})
    event = {"symbol": "TEST", "event_id": "1", "kind": "filing",
             "source": "issuer", "source_url": "https://example.org/filing",
             "published_at": "2026-10-01T12:00:00Z",
             "first_observed_at": "2026-10-01T12:01:00Z",
             "release_timestamp_verified": True}
    return {"events": [event], "bars_by_symbol": {"TEST": bars}}

class VerifiedEventRunnerTests(unittest.TestCase):
    def test_measures_actual_supplied_bars(self):
        result = run_verified_event_study(payload(),
            as_of_at="2026-10-20T00:00:00Z", minimum_events=2)
        self.assertEqual(result["events_accepted"], 1)
        self.assertGreater(result["outcome_rows"], 0)
        self.assertFalse(result["predictive_edge_proven"])
        self.assertFalse(result["cohorts"]["3"]["sufficient_sample"])
    def test_cutoff_blocks_future_exit(self):
        result = run_verified_event_study(payload(),
            as_of_at="2026-10-02T00:00:00Z", minimum_events=2)
        self.assertEqual(result["outcome_rows"], 0)
    def test_rejects_unverified_event(self):
        data = payload()
        data["events"][0]["release_timestamp_verified"] = False
        with self.assertRaisesRegex(ValueError, "unverified_release_time"):
            run_verified_event_study(data, as_of_at="2026-10-20T00:00:00Z")
    def test_uses_original_event_availability_not_a_reconstructed_time(self):
        data = payload()
        data["events"][0]["published_at"] = "2026-10-05T17:00:00Z"
        data["events"][0]["first_observed_at"] = "2026-10-05T17:01:00Z"
        result = run_verified_event_study(
            data, as_of_at="2026-10-20T00:00:00Z", minimum_events=2)
        self.assertGreater(result["outcome_rows"], 0)
        # Publication after the fifth session close: next decision is sixth close;
        # entry therefore cannot occur before seventh session open.
        self.assertEqual(result["cohorts"]["3"]["event_count"], 1)
    def test_future_publication_rejected(self):
        data = payload()
        data["events"][0]["published_at"] = "2026-10-21T12:00:00Z"
        data["events"][0]["first_observed_at"] = "2026-10-21T12:01:00Z"
        with self.assertRaisesRegex(ValueError, "event_after_cutoff"):
            run_verified_event_study(data, as_of_at="2026-10-20T00:00:00Z")
    def test_missing_prices_reported(self):
        data = payload()
        data["bars_by_symbol"] = {}
        result = run_verified_event_study(data, as_of_at="2026-10-20T00:00:00Z")
        self.assertEqual(result["events_missing_prices"], 1)

if __name__ == "__main__":
    unittest.main()
