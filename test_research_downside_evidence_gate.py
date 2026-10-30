import unittest
from research_downside_evidence_gate import downside_evidence_gate


class DownsideEvidenceGateTests(unittest.TestCase):
    def setUp(self):
        self.stock = [{"date": f"2026-01-{d:02d}", "close": str(100 + d)}
                      for d in range(1, 29)]
        self.spy = [{"date": r["date"], "close": "100"} for r in self.stock]

    def test_small_sample_blocks_evidence(self):
        result = downside_evidence_gate(self.stock, self.spy)
        self.assertFalse(result["sample_size_sufficient"])
        self.assertFalse(result["descriptive_evidence_sufficient"])
        self.assertIn("insufficient_group_samples", result["reasons"])
        self.assertEqual(result["additional_positive_windows_needed"],
                         30 - result["positive_count"])
        self.assertEqual(result["additional_negative_windows_needed"],
                         30 - result["negative_count"])
        self.assertTrue(result["sample_target_is_heuristic_not_power_analysis"])
        self.assertFalse(result["trade_ready"])

    def test_invalid_minimum(self):
        for value in (0, -1, True, 2.5):
            with self.subTest(value=value):
                with self.assertRaisesRegex(ValueError, "invalid_minimum_per_group"):
                    downside_evidence_gate(self.stock, self.spy, minimum_per_group=value)


if __name__ == "__main__":
    unittest.main()
