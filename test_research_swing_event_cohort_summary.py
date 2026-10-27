"""Regression tests for descriptive event cohort statistics."""
import unittest
from research_swing_event_cohort_summary import summarize_event_cohort

def row(event_id, entry, net, mae, symbol="ABC"):
    return {"event_id": event_id, "symbol": symbol, "horizon": 3,
            "entry_index": entry, "exit_index": entry + 3,
            "net_return_pct": net, "worst_intratrade_excursion_pct": mae}

class EventCohortTests(unittest.TestCase):
    def test_small_sample_has_no_return_estimate(self):
        result = summarize_event_cohort([row("a", 1, 10, -1)], horizon=3, minimum_events=2)
        self.assertFalse(result["sufficient_sample"])
        self.assertNotIn("mean_net_return_pct", result)
    def test_descriptive_rates(self):
        result = summarize_event_cohort([row("a", 1, 2, -1), row("b", 5, -4, -6)],
                                        horizon=3, minimum_events=2)
        self.assertEqual(result["mean_net_return_pct"], -1)
        self.assertEqual(result["historical_loss_fraction"], 0.5)
        self.assertEqual(result["historical_mae_below_minus_5_fraction"], 0.5)
        self.assertFalse(result["trade_ready"])
    def test_overlapping_windows_rejected(self):
        with self.assertRaisesRegex(ValueError, "overlapping_event_windows"):
            summarize_event_cohort([row("a", 1, 1, -1), row("b", 3, 2, -2)], horizon=3)
    def test_duplicate_events_rejected(self):
        with self.assertRaisesRegex(ValueError, "duplicate_event"):
            summarize_event_cohort([row("a", 1, 1, -1), row("a", 5, 2, -2)], horizon=3)
    def test_separate_symbols_can_share_indices(self):
        result = summarize_event_cohort([row("a", 1, 1, -1), row("b", 1, 2, -2, "XYZ")],
                                        horizon=3, minimum_events=2)
        self.assertEqual(result["event_count"], 2)

if __name__ == "__main__":
    unittest.main()
