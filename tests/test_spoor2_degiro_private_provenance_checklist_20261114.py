import unittest
from research.spoor2_degiro_private_provenance_checklist_20261114 import (
    REQUIRED_CHECKS, assess_provenance_checklist as assess,
)
ISIN = "DE0006231004"
TYPE = "BROKER_EXECUTION_CONFIRMATION"
DATE = "2026-11-14"

class PrivateProvenanceChecklistTests(unittest.TestCase):
    def test_empty_checklist_blocked(self):
        out = assess(ISIN, TYPE, [], DATE)
        self.assertFalse(out["checklist_complete"])
        self.assertFalse(out["trade_ready"])

    def test_complete_declarations_still_not_authenticated(self):
        out = assess(ISIN, TYPE, list(REQUIRED_CHECKS), DATE)
        self.assertTrue(out["checklist_complete"])
        for key in ("independently_authenticated", "broker_route_verified",
                    "degiro_fee_verified", "trade_ready", "order_placement_enabled"):
            self.assertFalse(out[key])

    def test_sensitive_key_rejected_without_echo(self):
        out = assess(ISIN, TYPE, ["account_number"], DATE)
        self.assertIn("UNEXPECTED_OR_SENSITIVE_CHECKLIST_KEYS", out["blocks"])
        self.assertNotIn("account_number", str(out))

    def test_unknown_check_rejected(self):
        out = assess(ISIN, TYPE, ["verified_by_me"], DATE)
        self.assertIn("UNEXPECTED_OR_SENSITIVE_CHECKLIST_KEYS", out["blocks"])

    def test_invalid_date_blocked(self):
        out = assess(ISIN, TYPE, list(REQUIRED_CHECKS), "2026/11/14")
        self.assertFalse(out["checklist_complete"])

    def test_missing_date_blocked(self):
        self.assertIn("REVIEW_DATE_MISSING", assess(ISIN, TYPE, [], None)["blocks"])

    def test_unknown_document_type_blocked(self):
        out = assess(ISIN, "SCREENSHOT", list(REQUIRED_CHECKS), DATE)
        self.assertFalse(out["checklist_complete"])

    def test_unknown_isin_blocked(self):
        self.assertIn("UNKNOWN_PILOT_ISIN", assess("INVALID", TYPE, [], DATE)["blocks"])

    def test_non_string_checklist_rejected(self):
        out = assess(ISIN, TYPE, ["broker_origin_checked_outside_public_repository", 12], DATE)
        self.assertIn("INVALID_CHECKLIST_INPUT", out["blocks"])

if __name__ == "__main__":
    unittest.main()
