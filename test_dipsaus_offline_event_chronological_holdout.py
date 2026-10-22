import unittest
from datetime import date, timedelta
from dipsaus_offline_event_chronological_holdout import chronological_holdout


def sample(n=120, falling=False):
    result = []
    for i in range(n):
        p = 200 - i if falling else 100 + i
        result.append({"date": (date(2025, 1, 1) + timedelta(days=i)).isoformat(),
                       "open": p, "high": p + 1, "low": p - 1,
                       "close": p, "volume": 1000})
    return result


class ChronologicalHoldoutTests(unittest.TestCase):
    def test_frozen_rule_and_chronological_boundary(self):
        out = chronological_holdout(sample())
        self.assertEqual(out["status"], "DESCRIPTIVE_CHRONOLOGICAL_SPLIT")
        self.assertLess(out["train_end_date"], out["test_start_date"])
        self.assertFalse(out["predictive_edge_proven"])
        self.assertFalse(out["trade_ready"])
        self.assertFalse(out["test_set_independent_of_development"])
        self.assertTrue(out["rule_frozen"])

    def test_no_signals_still_valid_split(self):
        out = chronological_holdout(sample(falling=True))
        self.assertEqual(out["status"], "DESCRIPTIVE_CHRONOLOGICAL_SPLIT")
        self.assertEqual(out["test"]["count"], 0)
        self.assertIsNone(out["test"]["mean_net_pct"])

    def test_bad_input_blocks(self):
        self.assertEqual(chronological_holdout([])["status"], "DATA_BLOCKED")
        self.assertEqual(chronological_holdout(sample(), horizon=0)["status"], "DATA_BLOCKED")


if __name__ == "__main__":
    unittest.main()
