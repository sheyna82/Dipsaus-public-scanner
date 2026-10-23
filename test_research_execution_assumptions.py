"""Deterministic research-only execution assumption regression tests."""

import unittest

from research_execution_assumptions import compare_execution_assumptions


class ExecutionAssumptionsTests(unittest.TestCase):
    def test_close_entry_overstates_return_after_gap(self):
        result = compare_execution_assumptions(
            signal_close=100, next_open=110, next_high=121, next_low=108,
            target_limit=120, spread_bps=10, fee_bps=10,
        )
        self.assertTrue(result["limit_price_touched"])
        self.assertGreater(
            result["optimistic_close_to_target_net_pct"],
            result["next_open_to_target_net_pct_if_filled"],
        )
        self.assertFalse(result["fill_verified"])

    def test_unreached_limit_has_no_realized_result(self):
        result = compare_execution_assumptions(
            signal_close=100, next_open=101, next_high=104, next_low=99,
            target_limit=105,
        )
        self.assertFalse(result["limit_price_touched"])
        self.assertIsNone(result["next_open_to_target_net_pct_if_filled"])

    def test_bad_candle_rejected(self):
        with self.assertRaises(ValueError):
            compare_execution_assumptions(
                signal_close=100, next_open=101, next_high=99,
                next_low=98, target_limit=110,
            )

    def test_negative_cost_rejected(self):
        with self.assertRaises(ValueError):
            compare_execution_assumptions(
                signal_close=100, next_open=101, next_high=103,
                next_low=99, target_limit=102, fee_bps=-1,
            )


if __name__ == "__main__":
    unittest.main()
