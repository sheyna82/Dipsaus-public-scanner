"""No preflight metadata can authorize a live probe or trading."""
import unittest
from research.us_live_provider_preflight_20261117 import review_live_provider_preflight

class ProviderPreflightTests(unittest.TestCase):
    def test_missing_record_blocks(self):
        r = review_live_provider_preflight(None)
        self.assertIn("MISSING_ENTITLEMENT_REFERENCE", r["blocks"])
        self.assertIn("ENDPOINT_MISSING", r["blocks"])
        self.assertFalse(r["network_access"])
        self.assertFalse(r["trade_ready"])

    def test_complete_self_report_never_authorizes(self):
        r = review_live_provider_preflight({
            "provider": "example", "account_plan_reference": "account-review",
            "entitlement_reference": "contract-review",
            "license_scope_reference": "terms-review",
            "private_execution_boundary": "private-only",
            "credential_storage_reference": "secret-manager",
            "data_retention_policy_reference": "no-public-retention",
            "endpoint": "https://example.org/v2/aggs",
            "public_ci_live_data": False,
            "public_logs_contain_market_data": False,
            "credential_in_source": False})
        self.assertEqual(r["status"], "LIVE_PROBE_BLOCKED")
        self.assertIn("DATA_LICENSE_NOT_INDEPENDENTLY_VERIFIED", r["blocks"])
        self.assertFalse(r["network_access"])
        self.assertFalse(r["notify"])

    def test_endpoint_query_credentials_and_public_ci_block(self):
        r = review_live_provider_preflight({
            "endpoint": "https://example.org/v2/aggs?apiKey=secret",
            "public_ci_live_data": True,
            "public_logs_contain_market_data": True,
            "credential_in_source": True})
        self.assertIn("ENDPOINT_UNSAFE", r["blocks"])
        self.assertIn("PUBLIC_CI_LIVE_DATA_NOT_DISABLED", r["blocks"])
        self.assertIn("PUBLIC_LOG_MARKET_DATA_NOT_DISABLED", r["blocks"])
        self.assertIn("CREDENTIAL_IN_SOURCE_NOT_DISABLED", r["blocks"])

    def test_url_userinfo_and_fragment_block(self):
        for url in ("https://name:password@example.org/data",
                    "https://example.org/data#fragment",
                    "http://example.org/data",
                    "https://[broken/data"):
            with self.subTest(url=url):
                r = review_live_provider_preflight({"endpoint": url})
                self.assertIn("ENDPOINT_UNSAFE", r["blocks"])
                self.assertFalse(r["network_access"])

if __name__ == "__main__":
    unittest.main()
