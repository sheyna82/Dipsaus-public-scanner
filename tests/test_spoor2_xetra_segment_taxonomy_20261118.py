"""Offline tests: venue-level segment codes cannot certify an instrument."""
import unittest
from research.spoor2_xetra_segment_taxonomy_20261118 import build_xetra_segment_taxonomy


class XetraSegmentTaxonomyTests(unittest.TestCase):
    def test_two_xetra_pilots_only(self):
        rows = build_xetra_segment_taxonomy()["rows"]
        self.assertEqual({r["isin_claim"] for r in rows},
                         {"DE0006231004", "DE0007030009"})

    def test_on_book_off_book_midpoint_are_distinct(self):
        mapping = build_xetra_segment_taxonomy()["rows"][0]["possible_segment_codes_by_trade_type"]
        self.assertEqual(mapping["on_book"], {"regulated": "XETA", "open_market": "XETB", "scale": "XETS"})
        self.assertEqual(mapping["off_book_lis"], {"regulated": "XETU", "open_market": "XETV", "scale": "XETW"})
        self.assertEqual(mapping["midpoint"], {"regulated": "XEMA", "open_market": "XEMB", "scale": "XEMI"})

    def test_never_infer_actual_segment(self):
        result = build_xetra_segment_taxonomy()
        for row in result["rows"]:
            self.assertIsNone(row["actual_segment_mic"])
            self.assertIsNone(row["instrument_market_segment"])
            self.assertIsNone(row["trade_type"])
            self.assertFalse(row["segment_mic_verified"])
        for gate in ("source_attested", "instrument_segment_verified", "segment_mic_verified",
                     "broker_route_verified", "degiro_fee_verified", "trade_ready",
                     "order_placement_enabled", "notify", "automatic_orders"):
            self.assertFalse(result[gate])


if __name__ == "__main__":
    unittest.main()
