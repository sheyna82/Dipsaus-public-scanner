import unittest
from research.spoor2_xetra_redirect_policy_20261114 import assess_xetra_redirect as assess
BASE = "https://www.cashmarket.deutsche-boerse.com/resource/blob/1528/" + "a"*32 + "/data/t7-xetr-allTradableInstruments.csv"
class RedirectPolicyTests(unittest.TestCase):
    def test_default_deny(self):
        self.assertFalse(assess("csv", BASE)["eligible_for_manual_second_request"])
    def test_exact_approved_still_unattested(self):
        r = assess("csv", BASE, (BASE,))
        self.assertTrue(r["eligible_for_manual_second_request"])
        for k in ("source_attested", "trade_ready", "order_placement_enabled", "broker_route_verified"):
            self.assertFalse(r[k])
    def test_approved_wrong_blob_id_still_rejected(self):
        x = BASE.replace("/blob/1528/", "/blob/9999/")
        result = assess("csv", x, (x,))
        self.assertFalse(result["eligible_for_manual_second_request"])
        self.assertIn("REDIRECT_TARGET_NOT_OFFICIAL_OR_UNSAFE", result["blocks"])
        self.assertFalse(result["source_attested"])

    def test_approved_wrong_filename_still_rejected(self):
        x = BASE.replace("t7-xetr-allTradableInstruments.csv", "other.csv")
        self.assertFalse(assess("csv", x, (x,))["eligible_for_manual_second_request"])

    def test_approved_noncanonical_token_still_rejected(self):
        x = BASE.replace("a"*32, "short")
        self.assertFalse(assess("csv", x, (x,))["eligible_for_manual_second_request"])

    def test_approved_control_character_still_rejected(self):
        x = BASE.replace("/data/", "/data/\t")
        self.assertFalse(assess("csv", x, (x,))["eligible_for_manual_second_request"])

    def test_other_host(self):
        self.assertFalse(assess("csv", "https://evil.example/resource/blob/file", (BASE,))["eligible_for_manual_second_request"])
    def test_http(self):
        self.assertFalse(assess("csv", BASE.replace("https:", "http:"), (BASE,))["eligible_for_manual_second_request"])
    def test_query_rejected(self):
        self.assertFalse(assess("csv", BASE+"?token=x", (BASE+"?token=x",))["eligible_for_manual_second_request"])
    def test_non_resource_path(self):
        x="https://www.cashmarket.deutsche-boerse.com/login"
        self.assertFalse(assess("csv", x, (x,))["eligible_for_manual_second_request"])
    def test_path_traversal_rejected_even_if_approved(self):
        x = "https://www.cashmarket.deutsche-boerse.com/resource/blob/../login"
        r = assess("csv", x, (x,))
        self.assertFalse(r["eligible_for_manual_second_request"])
        self.assertIn("REDIRECT_TARGET_NOT_OFFICIAL_OR_UNSAFE", r["blocks"])

    def test_percent_encoded_path_rejected_even_if_approved(self):
        x = "https://www.cashmarket.deutsche-boerse.com/resource/blob/%2e%2e/login"
        r = assess("csv", x, (x,))
        self.assertFalse(r["eligible_for_manual_second_request"])
        self.assertFalse(r["source_attested"])

    def test_backslash_path_rejected_even_if_approved(self):
        x = "https://www.cashmarket.deutsche-boerse.com/resource/blob/\\\\other"
        r = assess("csv", x, (x,))
        self.assertFalse(r["eligible_for_manual_second_request"])
        self.assertFalse(r["trade_ready"])

    def test_unknown_kind(self):
        self.assertIn("UNKNOWN_XETRA_ARTIFACT", assess("other", BASE)["blocks"])
    def test_unhashable_kind_fails_closed(self):
        r = assess(["csv"], BASE)
        self.assertIn("UNKNOWN_XETRA_ARTIFACT", r["blocks"])
        self.assertIsNone(r["kind"])
        self.assertFalse(r["eligible_for_manual_second_request"])
        self.assertFalse(r["trade_ready"])
    def test_invalid_policy_type(self):
        self.assertIn("INVALID_REDIRECT_POLICY_INPUT", assess("csv", BASE, [BASE])["blocks"])
    def test_malformed_port_fails_closed(self):
        x = "https://www.cashmarket.deutsche-boerse.com:bad/resource/blob/1528/new/data/file.csv"
        r = assess("csv", x, (x,))
        self.assertFalse(r["eligible_for_manual_second_request"])
        self.assertIn("MALFORMED_REDIRECT_TARGET", r["blocks"])
        self.assertFalse(r["trade_ready"])
    def test_out_of_range_port_fails_closed(self):
        x = "https://www.cashmarket.deutsche-boerse.com:99999/resource/blob/1528/new/data/file.csv"
        r = assess("csv", x, (x,))
        self.assertFalse(r["eligible_for_manual_second_request"])
        self.assertIn("MALFORMED_REDIRECT_TARGET", r["blocks"])
if __name__ == "__main__":
    unittest.main()
