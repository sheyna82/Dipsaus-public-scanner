"""Pin both real 2026-11-03 source observations and test their joint coverage."""
import unittest
from pathlib import Path
from research_verify_preserved_observation import verify_preserved_observation
from research_preserved_observation_report import assess_preserved_files

ROOT=Path(__file__).parent/"research-evidence"
AMD=ROOT/"amd-20261103-source-observation.json"
CSGP=ROOT/"csgp-20261103-source-observation.json"

class RealTwoSymbolEvidenceTests(unittest.TestCase):
    def test_original_csgp_file_pinned(self):
        report=verify_preserved_observation(
            CSGP,
            expected_json_sha256="dbbd06d6164f61b75dcda5aaf27abe3233481b9284c7df2a261749d9778b37c0",
            expected_source_sha256="18dc9e8994fcd6ec04ca839fbcb79fc01b367f91190c67df1af1a3638030729b")
        self.assertEqual(report["symbol"],"CSGP")
        self.assertFalse(report["quote_accuracy_verified"])
        self.assertFalse(report["trade_ready"])

    def test_both_real_observations_are_one_day(self):
        report=assess_preserved_files([AMD,CSGP])
        inventory=report["inventory"]
        coverage=report["coverage"]
        self.assertEqual(inventory["count"],2)
        self.assertEqual({x["symbol"] for x in inventory["observations"]},{"AMD","CSGP"})
        self.assertEqual(coverage["observation_count"],2)
        self.assertEqual(coverage["distinct_symbols"],2)
        self.assertEqual(coverage["distinct_utc_days"],1)
        self.assertFalse(coverage["coverage_thresholds_met"])
        self.assertFalse(coverage["prospective_edge_proven"])
        self.assertFalse(report["trade_ready"])

    def test_duplicate_csgp_rejected(self):
        with self.assertRaisesRegex(ValueError,"duplicate_observation_window"):
            assess_preserved_files([AMD,CSGP,CSGP])

if __name__=="__main__": unittest.main()
