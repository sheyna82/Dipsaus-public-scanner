import unittest
from research_chronological_momentum_holdout import chronological_momentum_holdout


class ChronologicalMomentumHoldoutTests(unittest.TestCase):
    def setUp(self):
        self.stock = [{"date": f"2026-01-{day:02d}", "close": str(100 + day)}
                      for day in range(1, 29)]
        self.spy = [{"date": row["date"], "close": "100"} for row in self.stock]

    def test_purges_cross_boundary_training_labels(self):
        result = chronological_momentum_holdout(self.stock, self.spy)
        self.assertGreater(result["purged_training_observations"], 0)
        self.assertGreater(result["training"]["observations"], 0)
        self.assertGreater(result["holdout"]["observations"], 0)
        self.assertFalse(result["predictive_skill_established"])
        self.assertFalse(result["trade_ready"])

    def test_invalid_fraction(self):
        for value in (0, 1, -0.1, True):
            with self.subTest(value=value):
                with self.assertRaisesRegex(ValueError, "invalid_train_fraction"):
                    chronological_momentum_holdout(self.stock, self.spy, train_fraction=value)

    def test_insufficient_data(self):
        with self.assertRaisesRegex(ValueError, "insufficient_holdout"):
            chronological_momentum_holdout(self.stock[:9], self.spy[:9])


if __name__ == "__main__":
    unittest.main()
