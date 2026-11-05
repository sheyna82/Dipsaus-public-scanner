import unittest
from dipsaus_offline_adjustment_factor_audit import audit_adjusted_close_factors


class AdjustmentFactorTests(unittest.TestCase):
    def test_constant_factor(self):
        result = audit_adjusted_close_factors([
            {"close": 100, "adjusted": 90}, {"close": 110, "adjusted": 99}])
        self.assertEqual(result["factor_change_events_gt_0_1pct"], 0)
        self.assertFalse(result["policy_verified"])

    def test_factor_jump(self):
        result = audit_adjusted_close_factors([
            {"close": 100, "adjusted": 90}, {"close": 100, "adjusted": 95}])
        self.assertEqual(result["factor_change_indices"], [1])

    def test_invalid_input(self):
        self.assertEqual(audit_adjusted_close_factors([
            {"close": 100, "adjusted": 90}, {"close": 0, "adjusted": 1}
        ])["status"], "REJECTED")


if __name__ == "__main__":
    unittest.main()
