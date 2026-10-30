import unittest
from dipsaus_offline_signal_control_comparison import compare_signal_controls


class SignalControlComparisonTests(unittest.TestCase):
    def test_balanced_groups_and_downside(self):
        rows = ([{"score": 5, "net_return_pct": 2, "max_adverse_excursion_pct": -3}] * 6
                + [{"score": 4, "net_return_pct": -1, "max_adverse_excursion_pct": -5}] * 6)
        result = compare_signal_controls(rows)
        self.assertEqual(result["status"], "EXPLORATORY_ONLY")
        self.assertEqual(result["mean_difference_pct_points"], 3)
        self.assertEqual(result["selected"]["mean_mae_pct"], -3)
        self.assertEqual(result["no_signal"]["mean_mae_pct"], -5)
        self.assertFalse(result["trade_ready"])

    def test_insufficient_sample(self):
        rows = [{"score": 5, "net_return_pct": 1}, {"score": 2, "net_return_pct": 0}]
        self.assertEqual(compare_signal_controls(rows)["status"], "INSUFFICIENT_SAMPLE")

    def test_invalid_rows(self):
        self.assertEqual(compare_signal_controls([{"score": 5}])["status"], "REJECTED")


if __name__ == "__main__":
    unittest.main()
