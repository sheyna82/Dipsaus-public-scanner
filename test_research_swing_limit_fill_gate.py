import unittest
from research_swing_limit_fill_gate import assess_limit_fill


class LimitFillGateTests(unittest.TestCase):
    def test_buy_strict_cross_not_confirmed(self):
        result = assess_limit_fill("buy", 100, 103, 104, 99,
                                   order_submitted_before_open=True)
        self.assertTrue(result["strictly_crossed_limit"])
        self.assertFalse(result["fill_confirmed"])

    def test_sell_strict_cross_not_confirmed(self):
        result = assess_limit_fill("sell", 105, 100, 106, 98,
                                   order_submitted_before_open=True)
        self.assertTrue(result["strictly_crossed_limit"])
        self.assertFalse(result["fill_confirmed"])

    def test_touch_only_not_strict_cross(self):
        result = assess_limit_fill("buy", 100, 103, 105, 100,
                                   order_submitted_before_open=True)
        self.assertTrue(result["limit_touched"])
        self.assertFalse(result["strictly_crossed_limit"])

    def test_no_touch(self):
        result = assess_limit_fill("sell", 110, 100, 105, 95,
                                   order_submitted_before_open=True)
        self.assertFalse(result["limit_touched"])

    def test_late_order_rejected(self):
        with self.assertRaisesRegex(ValueError, "preopen_order_timestamp_required"):
            assess_limit_fill("buy", 100, 100, 105, 95)

    def test_bad_ohlc_rejected(self):
        with self.assertRaisesRegex(ValueError, "invalid_ohlc"):
            assess_limit_fill("buy", 100, 110, 105, 95,
                              order_submitted_before_open=True)


if __name__ == "__main__":
    unittest.main()
