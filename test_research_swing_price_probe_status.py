import unittest
from urllib.error import HTTPError, URLError
from research_swing_price_probe_status import classify_price_probe_error


class PriceProbeStatusTests(unittest.TestCase):
    def test_network_error_is_not_market_data(self):
        result = classify_price_probe_error(URLError("DNS unavailable"))
        self.assertEqual(result["status"], "network_unavailable")
        self.assertFalse(result["data_verified"])

    def test_rate_limit_is_retryable(self):
        result = classify_price_probe_error(HTTPError("https://example.org", 429,
                                                       "rate limited", {}, None))
        self.assertTrue(result["retryable"])

    def test_invalid_csv_is_not_retryable(self):
        result = classify_price_probe_error(ValueError("unexpected_provider_header"))
        self.assertEqual(result["status"], "invalid_provider_data")
        self.assertFalse(result["retryable"])

    def test_not_found_not_retryable(self):
        result = classify_price_probe_error(HTTPError("https://example.org", 404,
                                                       "not found", {}, None))
        self.assertFalse(result["retryable"])


if __name__ == "__main__":
    unittest.main()
