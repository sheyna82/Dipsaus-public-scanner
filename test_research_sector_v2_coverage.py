import unittest
from research_swing_sector_universe_v2 import expanded_universe_manifest
from research_sector_v2_coverage import audit_exploratory_sector_coverage


class SectorV2CoverageTests(unittest.TestCase):
    def setUp(self):
        self.rows = {row["symbol"]: "normalized_unverified"
                     for row in expanded_universe_manifest()["symbols"]}

    def test_complete_unverified_research_is_not_trade_ready(self):
        result = audit_exploratory_sector_coverage(self.rows)
        self.assertEqual(result["status"], "REVIEW_REQUIRED")
        self.assertIs(result["source_data_validated"], False)
        self.assertIs(result["sector_representativeness_verified"], False)
        self.assertIs(result["trade_ready"], False)

    def test_missing_new_symbol_fails_closed(self):
        self.rows.pop("GOOGL")
        self.assertEqual(audit_exploratory_sector_coverage(self.rows)["status"], "UNKNOWN")

    def test_unavailable_data_flags_sector(self):
        self.rows["GOOGL"] = "unavailable"
        result = audit_exploratory_sector_coverage(self.rows)
        self.assertEqual(result["status"], "INCOMPLETE_RESEARCH")
        self.assertIn("communication_services", result["missing_sectors"])


if __name__ == "__main__":
    unittest.main()
