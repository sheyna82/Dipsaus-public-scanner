import unittest
from dipsaus_offline_earnings_coverage_gate import audit_calendar_coverage as check


class EarningsCoverageTests(unittest.TestCase):
    def test_no_inventory_fails_closed(self):
        self.assertEqual(check([], [], inventory_asof_verified=True, source_independent=True)["status"], "DATA_BLOCKED")

    def test_unverified_inventory_fails_closed(self):
        self.assertEqual(check(["A"], ["A"])["status"], "DATA_BLOCKED")

    def test_missing_issuer_detected(self):
        r = check(["A", "B"], ["A"], inventory_asof_verified=True, source_independent=True)
        self.assertEqual(r["status"], "COVERAGE_GAP")
        self.assertEqual(r["missing_issuer_ids"], ["B"])

    def test_matching_issuer_set_not_event_completeness(self):
        r = check(["A"], ["A"], inventory_asof_verified=True, source_independent=True)
        self.assertEqual(r["status"], "INVENTORY_MATCH")
        self.assertFalse(r["independent_event_completeness_verified"])
        self.assertFalse(r["trade_ready"])

    def test_bad_identifier_rejected(self):
        self.assertEqual(check([""], ["A"], inventory_asof_verified=True, source_independent=True)["status"], "DATA_BLOCKED")


if __name__ == "__main__":
    unittest.main()
