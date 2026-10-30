import unittest
from dipsaus_offline_downside_metrics import downside_metrics


class DownsideMetricsTests(unittest.TestCase):
    def test_fixed_severe_loss_threshold(self):
        result = downside_metrics([
            {"net_return_pct": 2.0},
            {"net_return_pct": -3.0},
            {"net_return_pct": -1.0},
            {"net_return_pct": -6.0}])
        self.assertEqual(result["severe_loss_count"], 2)
        self.assertEqual(result["severe_loss_fraction"], 0.5)
        self.assertEqual(result["any_loss_fraction"], 0.75)
        self.assertEqual(result["average_loss_pct"], -10 / 3)
        self.assertFalse(result["trade_ready"])

    def test_no_losses(self):
        result = downside_metrics([{"net_return_pct": 1}])
        self.assertIsNone(result["average_loss_pct"])

    def test_invalid_data_rejected(self):
        self.assertEqual(downside_metrics([{}])["status"], "REJECTED")


if __name__ == "__main__":
    unittest.main()
