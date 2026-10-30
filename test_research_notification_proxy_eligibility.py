import unittest
from research_notification_proxy_eligibility import audit_notification_proxy_outcomes

def outcome(**kwargs):
    value = {"research_only": True, "execution_verified": False,
             "entry_date": "2026-10-27", "exit_date": "2026-10-29",
             "net_proxy_return_pct": 1.2}
    value.update(kwargs)
    return value

class NotificationProxyEligibilityTests(unittest.TestCase):
    def test_missing_is_not_zero(self):
        r = audit_notification_proxy_outcomes("2026-10-26", {"EXE": {3: outcome()}})
        self.assertEqual(r["proxy_count"], 1)
        self.assertEqual(r["missing_count"], 3)
        self.assertEqual(r["verified_trade_count"], 0)
    def test_reject_execution_claim(self):
        with self.assertRaises(ValueError):
            audit_notification_proxy_outcomes("2026-10-26", {"EXE": {3: outcome(execution_verified=True)}})
    def test_reject_early_entry(self):
        with self.assertRaises(ValueError):
            audit_notification_proxy_outcomes("2026-10-26", {"EXE": {3: outcome(entry_date="2026-10-26")}})
    def test_reject_nonfinite(self):
        with self.assertRaises(ValueError):
            audit_notification_proxy_outcomes("2026-10-26", {"EXE": {3: outcome(net_proxy_return_pct=float("nan"))}})
if __name__ == "__main__":
    unittest.main()
