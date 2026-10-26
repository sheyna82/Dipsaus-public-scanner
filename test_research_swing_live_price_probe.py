"""Offline checks for the metadata-only public-price probe.

Never make network requests in CI unit tests.
"""
import unittest
from unittest.mock import patch
from research_swing_live_price_probe import probe


class LiveProbeTests(unittest.TestCase):
    @patch("research_swing_live_price_probe.download_once")
    def test_success_reports_metadata_only(self, mock_download):
        mock_download.return_value = {
            "symbol": "aapl.us", "bars": 100,
            "first_session": "2026-01-01", "last_session": "2026-10-01",
            "raw_sha256": "a" * 64,
        }
        result = probe("aapl.us")
        self.assertEqual(result["status"], "validated_download")
        self.assertEqual(result["bars"], 100)
        self.assertNotIn("daily_closes", result)
        self.assertFalse(result["source_data_saved"])
        self.assertFalse(result["license_verified"])

    @patch("research_swing_live_price_probe.download_once")
    def test_failed_download_never_claims_success(self, mock_download):
        mock_download.side_effect = TimeoutError("timeout")
        result = probe("aapl.us")
        self.assertEqual(result["status"], "failed")
        self.assertFalse(result["data_verified"])
        self.assertFalse(result["source_data_saved"])

    @patch("research_swing_live_price_probe.download_once")
    def test_invalid_provider_data_not_claimed_as_success(self, mock_download):
        mock_download.side_effect = ValueError("unexpected_provider_header")
        result = probe("spy.us")
        self.assertEqual(result["status"], "failed")
        self.assertFalse(result["data_verified"])


if __name__ == "__main__":
    unittest.main()
