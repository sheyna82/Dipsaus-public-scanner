import unittest
from candidate_matched_count_placebo import placebo

class PlaceboTests(unittest.TestCase):
    def setUp(self):
        self.rows = [{"excess_pct": float(i)} for i in range(20)]

    def test_deterministic(self):
        a = placebo(self.rows, self.rows[:5], draws=100, seed=42)
        self.assertEqual(a, placebo(self.rows, self.rows[:5], draws=100, seed=42))
        self.assertFalse(a["trade_ready"])

    def test_insufficient(self):
        self.assertEqual(placebo(self.rows, self.rows[:1])["status"], "INSUFFICIENT_MATCHED_SAMPLE")

    def test_rejects_invalid(self):
        with self.assertRaises(ValueError):
            placebo([{"excess_pct": float("nan")}], self.rows[:1])

    def test_no_false_probability(self):
        result = placebo(self.rows, self.rows[-5:], draws=100)
        self.assertGreater(result["observed_percentile"], .95)
        self.assertNotIn("win_probability", result)

if __name__ == "__main__":
    unittest.main()
