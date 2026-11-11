"""No-network regression checks for ten market-data candidates."""
import unittest
from urllib.parse import urlparse
from research_market_provider_catalog import PROVIDERS, REQUIRED_CHECKS, candidate_report


class MarketProviderCatalogTests(unittest.TestCase):
    def test_at_least_ten_distinct_https_candidates(self):
        self.assertGreaterEqual(len(PROVIDERS), 10)
        endpoints = [entry["endpoint"] for entry in PROVIDERS.values()]
        self.assertEqual(len(set(endpoints)), len(endpoints))
        self.assertTrue(all(urlparse(url).scheme == "https" for url in endpoints))

    def test_catalog_does_not_claim_verification_or_enable_providers(self):
        report = candidate_report()
        self.assertFalse(report["provider_integrations_enabled"])
        self.assertFalse(report["verified_market_data_available"])
        self.assertFalse(report["trade_ready"])
        self.assertTrue(all(entry["verification"] == "pending"
                            for entry in PROVIDERS.values()))
        self.assertGreaterEqual(len(REQUIRED_CHECKS), 8)

    def test_no_credentials_in_catalog(self):
        for entry in PROVIDERS.values():
            self.assertFalse(any("token_value" in key or "secret_value" in key
                                 for key in entry))


if __name__ == "__main__":
    unittest.main()
