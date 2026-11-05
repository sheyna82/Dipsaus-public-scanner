import unittest
from research_nonoverlapping_momentum import nonoverlapping_momentum_summary


class NonoverlappingMomentumTests(unittest.TestCase):
    def setUp(self):
        self.stock = [{"date": f"2026-10-{day:02d}", "close": str(100 + day)}
                      for day in range(1, 20)]
        self.spy = [{"date": f"2026-10-{day:02d}", "close": "100"}
                    for day in range(1, 20)]

    def test_nonoverlapping_counts(self):
        result = nonoverlapping_momentum_summary(self.stock, self.spy)
        self.assertEqual(result["all_overlapping_observations"], 13)
        self.assertEqual(result["nonoverlapping_observations"], 5)
        self.assertEqual(result["positive_count"], 5)
        self.assertTrue(result["small_sample"])
        self.assertFalse(result["predictive_skill_established"])

    def test_insufficient_sessions_rejected(self):
        with self.assertRaisesRegex(ValueError, "insufficient"):
            nonoverlapping_momentum_summary(self.stock[:6], self.spy[:6])


if __name__ == "__main__":
    unittest.main()
