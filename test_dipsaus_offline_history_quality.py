import unittest
from dipsaus_offline_history_quality import audit_price_history


class HistoryQualityTests(unittest.TestCase):
    def test_gap_requires_review_not_assert_missing_exchange_sessions(self):
        result = audit_price_history([
            {"date": "2024-01-02", "close": 100},
            {"date": "2024-01-16", "close": 101}])
        self.assertEqual(result["findings"][0]["type"], "CALENDAR_GAP_REVIEW")
        self.assertFalse(result["findings"][0]["missing_trading_sessions_confirmed"])

    def test_price_jump_is_not_automatically_called_split(self):
        result = audit_price_history([
            {"date": "2024-01-02", "close": 100},
            {"date": "2024-01-03", "close": 49}])
        self.assertEqual(result["findings"][0]["type"], "PRICE_JUMP_REVIEW")
        self.assertFalse(result["findings"][0]["corporate_action_confirmed"])

    def test_normal_weekend_not_flagged(self):
        result = audit_price_history([
            {"date": "2024-01-05", "close": 100},
            {"date": "2024-01-08", "close": 101}])
        self.assertEqual(result["findings"], [])


if __name__ == "__main__":
    unittest.main()
