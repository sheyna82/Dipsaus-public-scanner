import unittest
from research.spoor2_xetra_redirect_policy_20261114 import assess_xetra_redirect as assess
BASE = "https://www.cashmarket.deutsche-boerse.com/resource/blob/1528/new/data/file.csv"
class RedirectPolicyTests(unittest.TestCase):
    def test_default_deny(self):
        self.assertFalse(assess("csv", BASE)["eligible_for_manual_second_request"])
    def test_exact_approved_still_unattested(self):
        r = assess("csv", BASE, (BASE,))
        self.assertTrue(r["eligible_for_manual_second_request"])
        for k in ("source_attested", "trade_ready", "order_placement_enabled", "broker_route_verified"):
            self.assertFalse(r[k])
    def test_other_host(self):
        self.assertFalse(assess("csv", "https://evil.example/resource/blob/file", (BASE,))["eligible_for_manual_second_request"])
    def test_http(self):
        self.assertFalse(assess("csv", BASE.replace("https:", "http:"), (BASE,))["eligible_for_manual_second_request"])
    def test_query_rejected(self):
        self.assertFalse(assess("csv", BASE+"?token=x", (BASE+"?token=x",))["eligible_for_manual_second_request"])
    def test_non_resource_path(self):
        x="https://www.cashmarket.deutsche-boerse.com/login"
        self.assertFalse(assess("csv", x, (x,))["eligible_for_manual_second_request"])
    def test_unknown_kind(self):
        self.assertIn("UNKNOWN_XETRA_ARTIFACT", assess("other", BASE)["blocks"])
    def test_invalid_policy_type(self):
        self.assertIn("INVALID_REDIRECT_POLICY_INPUT", assess("csv", BASE, [BASE])["blocks"])
if __name__ == "__main__":
    unittest.main()
