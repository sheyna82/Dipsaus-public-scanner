"""Ensure unreviewed providers never become active automatically."""
import unittest
from research_swing_historical_source_registry import (
    source_review_status, eligible_automatic_sources)

class SourceRegistryTests(unittest.TestCase):
    def test_no_unreviewed_automatic_sources(self):
        self.assertEqual(eligible_automatic_sources(), ())
    def test_registry_covers_us_and_europe(self):
        sources = source_review_status()
        self.assertIn("sec_edgar", sources)
        self.assertIn("euronext_market_data", sources)
    def test_review_snapshot_is_independent(self):
        sources = source_review_status()
        sources["sec_edgar"]["automatic_ingestion_enabled"] = True
        self.assertFalse(source_review_status()["sec_edgar"]["automatic_ingestion_enabled"])

if __name__ == "__main__":
    unittest.main()
