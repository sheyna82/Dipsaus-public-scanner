"""Synthetic compatibility checks for frozen prospective momentum candidates."""
import unittest
from research_swing_ledger_compatibility import inspect_momentum_candidate


def candidate():
    return {"protocol_id": "frozen-test", "symbol": "EXAMPLE",
            "signal_session": "2026-10-26",
            "signal_positive_past_excess": True,
            "past_stock_return": "0.05", "past_spy_return": "0.02",
            "future_outcome": None, "future_outcome_available": False,
            "research_only": True, "trade_ready": False,
            "input_verified_independently": False}


class CompatibilityTests(unittest.TestCase):
    def test_binary_observation_not_a_swing_trade(self):
        result = inspect_momentum_candidate(candidate())
        self.assertTrue(result["compatible_as_binary_momentum_observation"])
        self.assertFalse(result["eligible_for_swing_portfolio"])
        self.assertIn("execution_entry_price", result["missing_for_swing"])

    def test_inconsistent_signal_rejected(self):
        x = candidate()
        x["signal_positive_past_excess"] = False
        with self.assertRaisesRegex(ValueError, "inconsistent_binary_signal"):
            inspect_momentum_candidate(x)

    def test_future_outcome_leak_rejected(self):
        x = candidate()
        x["future_outcome"] = "0.1"
        x["future_outcome_available"] = True
        with self.assertRaisesRegex(ValueError, "candidate_contains_future_outcome"):
            inspect_momentum_candidate(x)

    def test_trade_ready_candidate_rejected(self):
        x = candidate()
        x["trade_ready"] = True
        with self.assertRaisesRegex(ValueError, "unsafe_live_candidate"):
            inspect_momentum_candidate(x)

    def test_missing_field_rejected(self):
        x = candidate()
        del x["past_spy_return"]
        with self.assertRaisesRegex(ValueError, "missing_frozen_candidate_field"):
            inspect_momentum_candidate(x)


if __name__ == "__main__":
    unittest.main()
