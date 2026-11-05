import unittest
from datetime import datetime, timezone, timedelta
from sector_rotation_evidence import SECTORS, assess_sector_rotation


class SectorRotationEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 11, 2, 12, tzinfo=timezone.utc)
        self.stamp = self.now.isoformat()
        self.rows = {s: {"5d": 1.0, "10d": 1.0, "20d": 1.0} for s in SECTORS}

    def test_valid_research_not_trade_ready(self):
        result = assess_sector_rotation(self.rows, self.stamp, self.now)
        self.assertEqual(result["status"], "PASS")
        self.assertIs(result["trade_ready"], False)
        self.assertEqual(len(result["leaders"]), 3)

    def test_missing_sector_fails_closed(self):
        self.rows.pop("energy")
        self.assertEqual(assess_sector_rotation(self.rows, self.stamp, self.now)["status"], "UNKNOWN")

    def test_missing_period_fails_closed(self):
        self.rows["energy"].pop("10d")
        self.assertEqual(assess_sector_rotation(self.rows, self.stamp, self.now)["status"], "UNKNOWN")

    def test_stale_evidence_fails_closed(self):
        old = (self.now - timedelta(hours=1)).isoformat()
        self.assertEqual(assess_sector_rotation(self.rows, old, self.now)["status"], "UNKNOWN")

    def test_nonfinite_evidence_fails_closed(self):
        self.rows["energy"]["20d"] = float("nan")
        self.assertEqual(assess_sector_rotation(self.rows, self.stamp, self.now)["status"], "UNKNOWN")

    def test_tech_weakness_and_narrow_breadth_caution(self):
        for sector in list(SECTORS)[4:]:
            self.rows[sector]["20d"] = -1.0
        self.rows["technology"]["20d"] = -2.0
        result = assess_sector_rotation(self.rows, self.stamp, self.now)
        self.assertEqual(result["status"], "CAUTION")
        self.assertIs(result["trade_ready"], False)


if __name__ == "__main__":
    unittest.main()
