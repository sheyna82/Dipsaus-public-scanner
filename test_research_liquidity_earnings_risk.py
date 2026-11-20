import unittest
from research_liquidity_earnings_risk import screen_research_risks as screen

BASE = dict(bid=99.9, ask=100, average_daily_turnover_eur=2_000_000,
            relative_volume=1.5, earnings_calendar_checked=True,
            sessions_until_earnings=8)

class LiquidityEarningsRiskTests(unittest.TestCase):
    def test_normal_research_screen_never_authorizes_trades(self):
        r = screen(BASE)
        self.assertEqual(r["research_priority"], "ELIGIBLE_FOR_FURTHER_RESEARCH")
        self.assertFalse(r["trade_ready"])
        self.assertFalse(r["earnings_calendar_independently_verified"])

    def test_wide_spread_flags_liquidity(self):
        r = screen({**BASE, "bid": 98, "ask": 100})
        self.assertTrue(r["liquidity_warning"])
        self.assertEqual(r["research_priority"], "DEFER_FOR_REVIEW")

    def test_low_turnover_flags_liquidity(self):
        self.assertTrue(screen({**BASE, "average_daily_turnover_eur": 999999})["liquidity_warning"])

    def test_earnings_in_five_sessions_warns(self):
        r = screen({**BASE, "sessions_until_earnings": 5})
        self.assertTrue(r["earnings_within_five_sessions"])
        self.assertEqual(r["research_priority"], "DEFER_FOR_REVIEW")

    def test_six_sessions_does_not_warn(self):
        self.assertFalse(screen({**BASE, "sessions_until_earnings": 6})["earnings_within_five_sessions"])

    def test_missing_calendar_is_unknown_not_safe(self):
        r = screen({**BASE, "earnings_calendar_checked": False})
        self.assertIsNone(r["earnings_within_five_sessions"])
        self.assertEqual(r["research_priority"], "REVIEW_EARNINGS_UNKNOWN")

    def test_negative_sessions_block(self):
        self.assertEqual(screen({**BASE, "sessions_until_earnings": -1})["status"], "RISK_DATA_BLOCKED")

    def test_crossed_quotes_block(self):
        self.assertEqual(screen({**BASE, "bid": 101})["reason"], "INVALID_LIQUIDITY_RANGE")

    def test_nan_turnover_blocks(self):
        self.assertEqual(screen({**BASE, "average_daily_turnover_eur": float("nan")})["status"], "RISK_DATA_BLOCKED")

if __name__ == "__main__":
    unittest.main()
