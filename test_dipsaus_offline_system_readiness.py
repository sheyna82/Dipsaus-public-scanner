import unittest
from dipsaus_offline_system_readiness import audit_system, DIMENSIONS


class SystemReadinessTests(unittest.TestCase):
    def test_missing_evidence_cannot_pass(self):
        result = audit_system({})
        self.assertEqual(result["status"], "RESEARCH_INCOMPLETE")
        self.assertEqual(len(result["unknown"]), len(DIMENSIONS))
        self.assertFalse(result["trade_ready"])

    def test_one_failed_dimension_blocks_system(self):
        evidence = {key: {"status": "PASS", "source": "verified-ci-run"}
                    for key in DIMENSIONS}
        evidence["notification_delivery_reliability"]["status"] = "FAIL"
        result = audit_system(evidence)
        self.assertEqual(result["status"], "RESEARCH_BLOCKED")
        self.assertEqual(result["failed"], ["notification_delivery_reliability"])
        self.assertFalse(result["notify"])

    def test_unverified_pass_remains_unknown(self):
        result = audit_system({"multi_sector_chronological_holdout": {"status": "PASS"}})
        self.assertIn("multi_sector_chronological_holdout", result["unknown"])


if __name__ == "__main__":
    unittest.main()
