import unittest
from dipsaus_offline_readiness_report import readiness_report


class ReadinessReportTests(unittest.TestCase):
    def args(self):
        return dict(source_rows=[{"status": "OHLCV_VALIDATED"}],
                    earnings_asof={"status": "ASOF_ATTESTATION_ONLY"},
                    earnings_coverage={"status": "INVENTORY_MATCH"},
                    security_master={"status": "IDENTITY_REVIEW_REQUIRED"})

    def test_external_evidence_missing_is_named(self):
        r = readiness_report(**self.args())
        self.assertEqual(r["status"], "DATA_BLOCKED")
        self.assertIn("delisted_inventory_independently_verified", r["blocked_checks"])
        self.assertIn("corporate_actions_independently_verified", r["blocked_checks"])

    def test_bad_price_is_named(self):
        a = self.args()
        a["source_rows"] = [{"status": "DATA_BLOCKED"}]
        self.assertIn("price_history", readiness_report(**a)["blocked_checks"])

    def test_all_flags_still_require_independent_audit(self):
        r = readiness_report(**self.args(), corporate_actions_verified=True,
                             delisted_inventory_verified=True, holdout_frozen=True)
        self.assertEqual(r["status"], "MANUAL_INDEPENDENT_AUDIT_REQUIRED")
        self.assertFalse(r["predictive_edge_verified"])
        self.assertFalse(r["trade_ready"])


if __name__ == "__main__":
    unittest.main()
