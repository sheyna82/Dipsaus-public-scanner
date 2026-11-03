import json
import socket
import unittest
from unittest.mock import patch

from research_alpha_vantage_offline_daily import inspect_alpha_vantage_daily_bytes


class AlphaVantageOfflineTests(unittest.TestCase):
    def setUp(self):
        self.data = {
            "Meta Data": {"2. Symbol": "AMD"},
            "Time Series (Daily)": {
                "2026-11-03": {
                    "1. open": "100", "2. high": "104", "3. low": "99",
                    "4. close": "102", "5. volume": "12345"
                }
            },
        }

    def parse(self):
        return inspect_alpha_vantage_daily_bytes(
            json.dumps(self.data).encode(), expected_symbol="AMD",
            as_of_session="2026-11-03")

    def test_valid_fixture_without_network(self):
        with patch.object(socket, "getaddrinfo", side_effect=AssertionError("DNS")):
            with patch.object(socket.socket, "connect", side_effect=AssertionError("network")):
                result = self.parse()
        self.assertEqual(result["bar"]["close"], 102)
        self.assertFalse(result["provider_authenticity_verified"])
        self.assertFalse(result["trade_ready"])

    def test_rejects_provider_error(self):
        self.data = {"Note": "API rate limit"}
        with self.assertRaisesRegex(ValueError, "provider_error_or_rate_limit"):
            self.parse()

    def test_rejects_symbol_mismatch(self):
        self.data["Meta Data"]["2. Symbol"] = "IBM"
        with self.assertRaisesRegex(ValueError, "provider_symbol_mismatch"):
            self.parse()

    def test_rejects_future_bar(self):
        self.data["Time Series (Daily)"]["2026-11-04"] = self.data["Time Series (Daily)"]["2026-11-03"]
        with self.assertRaisesRegex(ValueError, "future_or_invalid_bar"):
            self.parse()

    def test_rejects_inconsistent_ohlc(self):
        self.data["Time Series (Daily)"]["2026-11-03"]["2. high"] = "98"
        with self.assertRaisesRegex(ValueError, "inconsistent_daily_bar"):
            self.parse()

    def test_rejects_missing_session(self):
        with self.assertRaisesRegex(ValueError, "requested_session_not_present"):
            inspect_alpha_vantage_daily_bytes(
                json.dumps(self.data).encode(), expected_symbol="AMD",
                as_of_session="2026-11-02")


if __name__ == "__main__":
    unittest.main()
