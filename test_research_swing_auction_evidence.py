"""Synthetic tests of opening-auction source classification."""
import unittest
from research_swing_auction_evidence import validate_auction_volume_evidence


def candidate():
    return {"ticker": "A", "auction_volume_source_kind":
            "official_exchange_opening_auction",
            "auction_volume_source_uri": "https://example.org/exchange/report",
            "auction_volume_session_date": "2026-10-02",
            "entry_session_date": "2026-10-02"}


class AuctionEvidenceTests(unittest.TestCase):
    def test_explicit_auction_source(self):
        result = validate_auction_volume_evidence([candidate()])
        self.assertTrue(result["opening_auction_source_type_checked"])
        self.assertFalse(result["source_authenticity_verified"])

    def test_daily_volume_proxy_rejected(self):
        x = candidate()
        x["auction_volume_source_kind"] = "daily_consolidated_volume"
        with self.assertRaisesRegex(ValueError, "opening_auction_volume_source_required"):
            validate_auction_volume_evidence([x])

    def test_intraday_volume_proxy_rejected(self):
        x = candidate()
        x["auction_volume_source_kind"] = "intraday_bar_volume"
        with self.assertRaisesRegex(ValueError, "opening_auction_volume_source_required"):
            validate_auction_volume_evidence([x])

    def test_missing_source_uri_rejected(self):
        x = candidate()
        x["auction_volume_source_uri"] = ""
        with self.assertRaisesRegex(ValueError, "invalid_source_uri"):
            validate_auction_volume_evidence([x])

    def test_other_session_rejected(self):
        x = candidate()
        x["auction_volume_session_date"] = "2026-10-01"
        with self.assertRaisesRegex(ValueError, "auction_volume_session_mismatch"):
            validate_auction_volume_evidence([x])

    def test_duplicate_ticker_rejected(self):
        with self.assertRaisesRegex(ValueError, "duplicate_or_invalid"):
            validate_auction_volume_evidence([candidate(), candidate()])


if __name__ == "__main__":
    unittest.main()
