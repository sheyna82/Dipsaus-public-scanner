import unittest
from research_swing_event_downside import event_downside_outcomes

class EventDownsideTests(unittest.TestCase):
    def bars(self):
        return [{"open":100.0, "low":99.0} for _ in range(20)]

    def test_no_future_signal_or_same_session_entry(self):
        result = event_downside_outcomes(self.bars(), known_session_index=2, horizons=(3,))
        self.assertEqual(result[0]["entry_index"], 3)
        self.assertEqual(result[0]["exit_index"], 6)
        self.assertFalse(result[0]["trade_ready"])

    def test_intratrade_dip_not_hidden_by_recovery(self):
        rows = self.bars()
        rows[4]["low"] = 87
        outcome = event_downside_outcomes(rows, known_session_index=2, horizons=(3,))[0]
        self.assertTrue(outcome["adverse_threshold_hits"]["10"])
        self.assertLess(outcome["worst_intratrade_excursion_pct"], -10)
        self.assertLess(outcome["net_return_pct"], 0)

    def test_later_future_change_cannot_rewrite_earlier_outcome(self):
        rows = self.bars()
        before = event_downside_outcomes(rows, known_session_index=2, horizons=(3,))[0]
        rows[15]["open"] = 500
        rows[15]["low"] = 450
        after = event_downside_outcomes(rows, known_session_index=2, horizons=(3,))[0]
        self.assertEqual(before, after)

    def test_no_partial_horizon_label(self):
        self.assertEqual(event_downside_outcomes(self.bars(), known_session_index=17,
                                                horizons=(3, 5)), [])

    def test_bad_threshold_rejected(self):
        with self.assertRaisesRegex(ValueError, "invalid_thresholds"):
            event_downside_outcomes(self.bars(), known_session_index=2,
                                    loss_thresholds_pct=(-5,))

if __name__ == "__main__":
    unittest.main()
