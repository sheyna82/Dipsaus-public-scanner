import unittest
from datetime import datetime, timezone
from research_swing_diversified_universe import UNIVERSE_V1
from sector_rotation_historical_bridge import (
    historical_sector_coverage, sector_rotation_from_historical_unverified)


class HistoricalSectorBridgeTests(unittest.TestCase):
    def test_existing_universe_has_explicit_missing_sectors(self):
        rows = {symbol: "normalized_unverified" for symbol, _ in UNIVERSE_V1}
        result = historical_sector_coverage(rows)
        self.assertEqual(result["status"], "INCOMPLETE_RESEARCH")
        self.assertEqual(result["missing_sectors"],
                         ["communication_services", "consumer_discretionary"])
        self.assertIs(result["trade_ready"], False)

    def test_missing_symbol_fails_closed(self):
        rows = {symbol: "normalized_unverified" for symbol, _ in UNIVERSE_V1}
        rows.pop("AMD")
        self.assertEqual(historical_sector_coverage(rows)["status"], "UNKNOWN")

    def test_unverified_historical_never_becomes_live_pass(self):
        now = datetime(2026, 11, 2, 12, tzinfo=timezone.utc)
        result = sector_rotation_from_historical_unverified(None, now.isoformat(), now)
        self.assertEqual(result["status"], "UNKNOWN")
        self.assertIs(result["trade_ready"], False)
        self.assertEqual(result["reason"], "HISTORICAL_UNVERIFIED_NOT_LIVE")


if __name__ == "__main__":
    unittest.main()
