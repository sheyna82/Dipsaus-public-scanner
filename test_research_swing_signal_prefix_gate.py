import unittest
from research_swing_signal_prefix_gate import validate_signal_prefix_consistency


class PrefixGateTests(unittest.TestCase):
    def test_causal_running_mean_passes(self):
        def causal(bars):
            return [sum(bars[:i + 1]) / (i + 1) for i in range(len(bars))]
        result = validate_signal_prefix_consistency([1, 2, 3, 4, 5], causal)
        self.assertTrue(result["lookahead_prefix_consistent"])
        self.assertEqual(result["violations"], [])

    def test_future_dependent_signal_fails(self):
        def leaking(bars):
            return [sum(bars) for _ in bars]
        result = validate_signal_prefix_consistency([1, 2, 3, 4], leaking)
        self.assertFalse(result["lookahead_prefix_consistent"])
        self.assertTrue(result["violations"])

    def test_wrong_output_length_rejected(self):
        with self.assertRaisesRegex(ValueError, "invalid_full_signal_output"):
            validate_signal_prefix_consistency([1, 2, 3], lambda bars: [])

    def test_nonfinite_signal_rejected(self):
        with self.assertRaisesRegex(ValueError, "invalid_signal_value"):
            validate_signal_prefix_consistency([1, 2, 3], lambda bars: [float("nan")] * len(bars))

    def test_insufficient_history_rejected(self):
        with self.assertRaisesRegex(ValueError, "insufficient_signal_history"):
            validate_signal_prefix_consistency([1], lambda bars: bars)


if __name__ == "__main__":
    unittest.main()
