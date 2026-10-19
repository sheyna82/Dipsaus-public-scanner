import unittest
from dipsaus_eur_upside_audit import audit_row, audit_rows


class AuditTests(unittest.TestCase):
    def test_missing_inputs_visible_without_fabrication(self):
        r = audit_row({"symbol": "RNG", "market": "US", "provider_quote": 79.36})
        self.assertEqual(r["status"], "UNKNOWN")
        self.assertIn("resistance_usd", r["missing_fields"])
        self.assertIn("eur_per_usd", r["missing_fields"])
        self.assertFalse(r["trade_ready"])

    def test_public_pivot_is_not_automatically_verified_resistance(self):
        r = audit_row({"symbol": "HTFL", "market": "US",
                       "route_2_break_above": 52.2, "provider_quote": 51.31})
        self.assertIn("resistance_usd", r["missing_fields"])

    def test_non_us_not_in_us_coverage(self):
        r = audit_rows([{"symbol": "ALFEN", "market": "EU"},
                        {"symbol": "EXE", "market": "US"}])
        self.assertEqual(r["total_us_rows"], 1)
        self.assertEqual(r["unavailable"], 1)


if __name__ == "__main__":
    unittest.main()
