import unittest
from research.spoor2_degiro_xetra_public_tariff_20261113 import assess_public_xetra_tariff

class PublicXetraTariffTests(unittest.TestCase):
    def test_public_fee_math(self):
        out = assess_public_xetra_tariff(execution_venue="XETRA")
        self.assertEqual(out["public_per_side_eur"], "4.90")
        self.assertEqual(out["public_round_trip_eur"], "9.80")
        self.assertTrue(out["public_schedule_applicable_by_date"])

    def test_public_document_never_authorizes_orders(self):
        out = assess_public_xetra_tariff(execution_venue="XETRA",
                                         account_tariff_evidence={"verified": True, "fee": "4.90"})
        for field in ("account_tariff_verified", "broker_route_verified",
                      "degiro_fee_verified", "trade_ready", "order_placement_enabled"):
            self.assertFalse(out[field])

    def test_non_xetra_venue_is_not_automatically_covered(self):
        out = assess_public_xetra_tariff(execution_venue="TRADEGATE")
        self.assertIn("XETRA_EXECUTION_VENUE_NOT_ACCOUNT_ATTESTED", out["blocks"])

    def test_undated_route_is_not_attested(self):
        out = assess_public_xetra_tariff()
        self.assertIn("XETRA_EXECUTION_VENUE_NOT_ACCOUNT_ATTESTED", out["blocks"])

    def test_historical_before_effective_date_rejected(self):
        out = assess_public_xetra_tariff(as_of="2025-12-31")
        self.assertFalse(out["public_schedule_applicable_by_date"])
        self.assertIsNone(out["public_per_side_eur"])

    def test_invalid_date_rejected(self):
        out = assess_public_xetra_tariff(as_of="13-11-2026")
        self.assertIn("INVALID_TARIFF_DATE", out["blocks"])

if __name__ == "__main__":
    unittest.main()
