"""Regression test using the original preserved AMD observation."""
import unittest
from pathlib import Path
from research_preserved_observation_report import assess_preserved_files

AMD=Path(__file__).parent/"research-evidence/amd-20261103-source-observation.json"

class RealCoverageTests(unittest.TestCase):
    def test_one_real_observation_does_not_pass_coverage(self):
        report=assess_preserved_files([AMD])
        self.assertEqual(report["inventory"]["count"],1)
        self.assertEqual(report["coverage"]["distinct_utc_days"],1)
        self.assertEqual(report["coverage"]["distinct_symbols"],1)
        self.assertFalse(report["coverage"]["coverage_thresholds_met"])
        self.assertFalse(report["trade_ready"])
        self.assertIn("INSUFFICIENT_OBSERVATIONS",report["coverage"]["blocking_reasons"])
    def test_duplicate_real_observation_rejected(self):
        with self.assertRaisesRegex(ValueError,"duplicate_observation_window"):
            assess_preserved_files([AMD,AMD])

if __name__=="__main__": unittest.main()
