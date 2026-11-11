import unittest
from dipsaus_offline_universe_coverage import audit_universe_coverage


class UniverseCoverageTests(unittest.TestCase):
    def test_empty_rejected(self):
        self.assertEqual(audit_universe_coverage([])["status"], "DATA_BLOCKED")

    def test_duplicates_rejected(self):
        self.assertEqual(audit_universe_coverage([{"symbol": "A"}, {"symbol": "A"}])["status"],
                         "DATA_BLOCKED")

    def test_includes_delisted_and_exclusions(self):
        rows = [
            {"symbol": "A", "listing_status": "active", "sector_at_sample_date": "Industrials"},
            {"symbol": "B", "listing_status": "delisted", "sector_at_sample_date": "Energy",
             "exclusion_reason": "missing_ohlcv"},
        ]
        report = audit_universe_coverage(rows, expected_total=3)
        self.assertEqual(report["listing_status_counts"]["delisted"], 1)
        self.assertEqual(report["unaccounted_securities"], 1)
        self.assertEqual(report["exclusion_reason_counts"]["missing_ohlcv"], 1)
        self.assertFalse(report["survivorship_bias_ruled_out"])

    def test_attested_coverage_never_claims_verification(self):
        report = audit_universe_coverage([{"symbol": "A", "listing_status": "delisted"}],
                                         expected_total=1)
        self.assertFalse(report["delisted_coverage_independently_verified"])
        self.assertFalse(report["trade_ready"])


if __name__ == "__main__":
    unittest.main()
