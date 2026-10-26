import unittest
from research_notification_signal_cases import CASES_2026_10_26, audit_cases

class NotificationCaseTests(unittest.TestCase):
    def test_eight_observed_signals(self):
        self.assertEqual(len(CASES_2026_10_26), 8)
        self.assertEqual(len({x.symbol for x in CASES_2026_10_26}), 8)

    def test_not_trade_ready(self):
        report = audit_cases()
        self.assertFalse(report["ready_for_net_return_study"])
        self.assertTrue(report["research_only"])
        self.assertIn("UTC event timestamp", report["missing"])

    def test_distinguish_signal_families(self):
        self.assertEqual(len(audit_cases()["families"]), 4)

if __name__ == "__main__":
    unittest.main()
