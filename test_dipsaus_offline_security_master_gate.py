import unittest
from dipsaus_offline_security_master_gate import audit_security_master as audit


class SecurityMasterGateTests(unittest.TestCase):
    def test_same_ticker_reused_in_different_periods_is_not_collision(self):
        rows = [
            {"security_id": "old", "ticker": "ABC", "listed_from": "1990-01-01", "listed_through": "2001-01-01"},
            {"security_id": "new", "ticker": "ABC", "listed_from": "2010-01-01", "listed_through": None},
        ]
        r = audit(rows, sample_date="2020-01-01", independent_inventory_verified=True)
        self.assertEqual(r["status"], "IDENTITY_REVIEW_REQUIRED")
        self.assertEqual(r["active_at_sample"], 1)
        self.assertFalse(r["survivorship_bias_ruled_out"])

    def test_concurrent_ticker_collision_blocks(self):
        rows = [
            {"security_id": "1", "ticker": "ABC", "listed_from": "2010-01-01", "listed_through": None},
            {"security_id": "2", "ticker": "ABC", "listed_from": "2010-01-01", "listed_through": None},
        ]
        self.assertEqual(audit(rows, sample_date="2020-01-01", independent_inventory_verified=True)["reason"],
                         "ticker_collision")

    def test_duplicate_stable_id_blocks(self):
        rows = [{"security_id": "x", "ticker": "A", "listed_from": "2000-01-01", "listed_through": None}] * 2
        self.assertEqual(audit(rows, sample_date="2020-01-01")["reason"], "duplicate_security_id")

    def test_missing_independent_inventory_blocks(self):
        rows = [{"security_id": "x", "ticker": "A", "listed_from": "2000-01-01", "listed_through": None}]
        self.assertEqual(audit(rows, sample_date="2020-01-01")["status"], "DATA_BLOCKED")

    def test_invalid_listing_range_blocks(self):
        rows = [{"security_id": "x", "ticker": "A", "listed_from": "2020-01-01", "listed_through": "2010-01-01"}]
        self.assertEqual(audit(rows, sample_date="2020-01-01")["status"], "DATA_BLOCKED")


if __name__ == "__main__":
    unittest.main()
