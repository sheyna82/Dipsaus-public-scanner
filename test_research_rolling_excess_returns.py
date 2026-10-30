import unittest
from research_rolling_excess_returns import rolling_excess_returns


class RollingExcessReturnsTests(unittest.TestCase):
    def setUp(self):
        self.stock = [{"date": f"2026-10-{day:02d}", "close": str(100 + day)} for day in range(1, 9)]
        self.spy = [{"date": f"2026-10-{day:02d}", "close": "100"} for day in range(1, 9)]

    def test_forward_returns_and_horizons(self):
        result = rolling_excess_returns(self.stock, self.spy)
        self.assertEqual(len(result["observations"]), 7 + 5 + 3)
        first = result["observations"][0]
        self.assertEqual((first["start_session"], first["end_session"], first["horizon"]),
                         ("2026-10-01", "2026-10-02", 1))
        self.assertGreater(float(first["excess_percentage_points"]), 0)
        self.assertFalse(result["predictive_skill_established"])

    def test_rejects_unordered_sessions(self):
        with self.assertRaisesRegex(ValueError, "invalid_order"):
            rolling_excess_returns(list(reversed(self.stock)), self.spy)

    def test_rejects_insufficient_overlap(self):
        with self.assertRaisesRegex(ValueError, "insufficient_shared_sessions"):
            rolling_excess_returns(self.stock[:2], self.spy[:2])

    def test_rejects_invalid_price(self):
        rows = [dict(row) for row in self.stock]
        rows[0]["close"] = "-1"
        with self.assertRaisesRegex(ValueError, "invalid_price"):
            rolling_excess_returns(rows, self.spy)


if __name__ == "__main__":
    unittest.main()
