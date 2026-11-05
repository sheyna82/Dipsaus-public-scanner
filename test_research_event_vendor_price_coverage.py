import unittest
from research_event_vendor_price_coverage import audit_event_price_metadata

class VendorCoverageTests(unittest.TestCase):
    def test_no_download_means_no_coverage(self):
        result = audit_event_price_metadata([])
        self.assertEqual(len(result), 4)
        self.assertTrue(all(not row["vendor_history_covers_alert_date"] for row in result))

    def test_metadata_coverage_is_not_signal_verification(self):
        metadata = [{"symbol": "TSLA", "first_observation_date": "2026-10-01",
                     "last_observation_date": "2026-10-26", "row_count": 15,
                     "content_sha256": "synthetic", "source_url": "https://stooq.com/example"}]
        result = audit_event_price_metadata(metadata)
        self.assertTrue(result[0]["vendor_history_covers_alert_date"])
        self.assertFalse(result[0]["vendor_source_independently_verified"])
        self.assertFalse(result[0]["trade_ready"])

    def test_invalid_date_range_does_not_count(self):
        metadata = [{"symbol": "META", "first_observation_date": "2026-10-23",
                     "last_observation_date": "2026-10-26", "row_count": 2,
                     "content_sha256": "synthetic", "source_url": "https://stooq.com/example"}]
        result = audit_event_price_metadata(metadata)
        self.assertFalse(next(row for row in result if row["ticker"] == "META")
                         ["vendor_history_covers_alert_date"])

if __name__ == "__main__":
    unittest.main()
