import unittest
from datetime import date, timedelta
from research_historical_ohlcv_horizon_gate import audit_daily_ohlcv_horizon

def row(symbol, day):
    return {"symbol": symbol, "date": day.isoformat(),
            "open": 10.0, "high": 11.0, "low": 9.0, "close": 10.5}

class HistoricalHorizonGateTests(unittest.TestCase):
    def test_three_day_repo_style_data_blocked(self):
        dates = [date(2026, 10, 21) + timedelta(days=i) for i in range(3)]
        result = audit_daily_ohlcv_horizon([row(s, d) for s in ("TSLA", "META", "AMZN", "COHU") for d in dates])
        self.assertFalse(result["all_symbols_eligible"])
        self.assertEqual(result["symbols"]["TSLA"]["sessions"], 3)

    def test_sixteen_sessions_pass_necessary_not_sufficient_gate(self):
        dates = [date(2026, 9, 1) + timedelta(days=i) for i in range(16)]
        result = audit_daily_ohlcv_horizon([row("AMD", d) for d in dates])
        self.assertTrue(result["all_symbols_eligible"])
        self.assertFalse(result["calendar_continuity_verified"])
        self.assertFalse(result["source_independently_verified"])

    def test_duplicate_session_rejected(self):
        x = row("AMD", date(2026, 10, 21))
        with self.assertRaisesRegex(ValueError, "DUPLICATE_OHLCV_SESSION"):
            audit_daily_ohlcv_horizon([x, x])

    def test_invalid_price_range_rejected(self):
        x = row("AMD", date(2026, 10, 21))
        x["low"] = 12.0
        with self.assertRaisesRegex(ValueError, "INVALID_OHLCV_RANGE"):
            audit_daily_ohlcv_horizon([x])

    def test_empty_rows_rejected(self):
        with self.assertRaisesRegex(ValueError, "EMPTY_OHLCV_ROWS"):
            audit_daily_ohlcv_horizon([])

if __name__ == "__main__":
    unittest.main()
