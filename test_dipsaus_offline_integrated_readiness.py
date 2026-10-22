import unittest
from dipsaus_offline_integrated_readiness import audit_integrated_readiness as audit


class IntegratedReadinessTests(unittest.TestCase):
    def inputs(self):
        return dict(source_rows=[{"status": "OHLCV_VALIDATED"}],
                    earnings_asof={"status": "ASOF_ATTESTATION_ONLY"},
                    earnings_coverage={"status": "INVENTORY_MATCH"},
                    security_master={"status": "IDENTITY_REVIEW_REQUIRED"},
                    independent_corporate_actions=True,
                    independent_delisted_inventory=True, frozen_holdout=True)

    def test_valid_structure_still_requires_independent_audit(self):
        result = audit(**self.inputs())
        self.assertEqual(result["status"], "MANUAL_INDEPENDENT_AUDIT_REQUIRED")
        self.assertFalse(result["predictive_edge_verified"])
        self.assertFalse(result["trade_ready"])

    def test_delisted_coverage_not_verified_blocks(self):
        args = self.inputs()
        args["independent_delisted_inventory"] = False
        self.assertEqual(audit(**args)["reason"], "external_evidence_missing")

    def test_bad_price_source_blocks(self):
        args = self.inputs()
        args["source_rows"] = [{"status": "DATA_BLOCKED"}]
        self.assertEqual(audit(**args)["reason"], "price_source_rejected")

    def test_missing_earnings_inventory_blocks(self):
        args = self.inputs()
        args["earnings_coverage"] = {"status": "COVERAGE_GAP"}
        self.assertEqual(audit(**args)["reason"], "earnings_inventory_unverified")

    def test_missing_security_master_blocks(self):
        args = self.inputs()
        args["security_master"] = {"status": "DATA_BLOCKED"}
        self.assertEqual(audit(**args)["reason"], "security_identity_unverified")


if __name__ == "__main__":
    unittest.main()
