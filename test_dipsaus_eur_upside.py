import unittest
from datetime import datetime, timezone, timedelta
from dipsaus_eur_upside import estimate_gross_eur, message_context


class EurUpsideTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 10, 19, 20, tzinfo=timezone.utc)
        stamp = self.now.isoformat()
        self.row = dict(market="US", provider_quote=80.0, resistance_usd=88.0,
                        invalidation_usd=77.0, eur_per_usd=0.92,
                        provider_freshness_pass=True,
                        resistance_verified=True, invalidation_verified=True,
                        provider_quote_utc=stamp, resistance_checked_utc=stamp,
                        invalidation_checked_utc=stamp, fx_checked_utc=stamp)

    def test_indicative_calculation_not_buy(self):
        result = estimate_gross_eur(self.row, now=self.now)
        self.assertEqual(result["status"], "RESEARCH_ESTIMATE")
        self.assertEqual(result["shares_estimate"], 47)
        self.assertEqual(result["gross_eur"], 345.92)
        self.assertEqual(result["risk_eur"], 129.72)
        self.assertFalse(result["trade_ready"])

    def test_no_target_no_claim(self):
        self.row.pop("resistance_usd")
        self.assertEqual(estimate_gross_eur(self.row, now=self.now)["status"], "UNKNOWN")

    def test_stale_fx_blocks(self):
        self.row["fx_checked_utc"] = (self.now-timedelta(minutes=16)).isoformat()
        self.assertEqual(estimate_gross_eur(self.row, now=self.now)["status"], "UNKNOWN")

    def test_unverified_resistance_blocks(self):
        self.row["resistance_verified"] = False
        self.assertEqual(estimate_gross_eur(self.row, now=self.now)["status"], "UNKNOWN")

    def test_bad_rr_structure_not_buy(self):
        self.row["resistance_usd"] = 79
        self.assertEqual(estimate_gross_eur(self.row, now=self.now)["status"], "UNFAVORABLE_STRUCTURE")

    def test_missing_fx_no_fake_eur(self):
        self.row.pop("eur_per_usd")
        self.assertIn("NIET BEREKENBAAR", message_context(self.row, now=self.now))

    def test_zero_risk_invalid(self):
        self.row["invalidation_usd"] = 80
        self.assertEqual(estimate_gross_eur(self.row, now=self.now)["status"], "UNFAVORABLE_STRUCTURE")


if __name__ == "__main__":
    unittest.main()
