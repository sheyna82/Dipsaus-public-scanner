import unittest
from research_swing_short_regime_gate import assess_short_swing_regime

class ShortRegimeGateTests(unittest.TestCase):
    def test_stable_market(self):
        r = assess_short_swing_regime([100 + i*.1 for i in range(80)])
        self.assertEqual(r["state"], "normal")
        self.assertEqual(r["preferred_horizons"], [5,10,15])
    def test_sharp_decline_blocks_new_entries(self):
        r = assess_short_swing_regime([100.0]*60 + [99.0-i for i in range(20)])
        self.assertEqual(r["state"], "risk_off")
        self.assertFalse(r["new_entries_permitted_for_research"])
    def test_invalid_prices_fail(self):
        with self.assertRaises(ValueError):
            assess_short_swing_regime([100.0]*59+[float("nan")])
    def test_short_history_fails(self):
        with self.assertRaises(ValueError):
            assess_short_swing_regime([100.0]*40)
if __name__ == "__main__":
    unittest.main()
