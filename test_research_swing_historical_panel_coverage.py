import unittest
from research_swing_historical_panel_coverage import audit_historical_panel

def bars(n):
    from datetime import date, timedelta
    return [{"date": (date(2025, 1, 1) + timedelta(days=i)).isoformat()} for i in range(n)]

class HistoricalPanelCoverageTests(unittest.TestCase):
    def test_missing_benchmark_blocks_complete(self):
        r = audit_historical_panel(["AAA"], ["SPY"], {"AAA": bars(4)}, min_sessions=3)
        self.assertFalse(r["length_coverage_complete"])
        self.assertEqual(r["rows"][1]["status"], "missing")
    def test_complete_length_is_not_verified(self):
        r = audit_historical_panel(["AAA"], ["SPY"], {"AAA": bars(4), "SPY": bars(4)}, min_sessions=3)
        self.assertTrue(r["length_coverage_complete"])
        self.assertFalse(r["source_provenance_verified"])
    def test_disjoint_dates_block_aligned_panel(self):
        other = [{"date": "2024-01-0" + str(i)} for i in range(1, 5)]
        r = audit_historical_panel(["AAA"], ["SPY"], {"AAA": bars(4), "SPY": other}, min_sessions=3)
        self.assertTrue(r["length_coverage_complete"])
        self.assertFalse(r["aligned_length_sufficient"])
        self.assertEqual(r["common_session_count"], 0)
    def test_aligned_sessions_sufficient(self):
        r = audit_historical_panel(["AAA"], ["SPY"], {"AAA": bars(4), "SPY": bars(4)}, min_sessions=3)
        self.assertTrue(r["aligned_length_sufficient"])
    def test_duplicate_dates_fail(self):
        with self.assertRaises(ValueError):
            audit_historical_panel(["AAA"], [], {"AAA": [bars(1)[0], bars(1)[0]]})
    def test_unexpected_symbol_fail(self):
        with self.assertRaises(ValueError):
            audit_historical_panel(["AAA"], [], {"AAA": bars(2), "BBB": bars(2)})
if __name__ == "__main__":
    unittest.main()
