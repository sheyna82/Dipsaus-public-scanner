import unittest
from research.spoor2_degiro_execution_confirmation_protocol_20261113 import (
    REQUIRED_FIELDS, assess_execution_confirmation_requirements as assess,
)
ISIN = "DE0006231004"

class ExecutionConfirmationProtocolTests(unittest.TestCase):
    def test_no_evidence_blocks(self):
        out = assess(ISIN)
        self.assertEqual(len(out["missing_fields"]), len(REQUIRED_FIELDS))
        self.assertFalse(out["trade_ready"])

    def test_complete_field_inventory_is_not_attestation(self):
        out = assess(ISIN, list(REQUIRED_FIELDS))
        self.assertTrue(out["metadata_complete"])
        self.assertFalse(out["document_authenticity_verified"])
        for k in ("account_execution_route_verified", "account_tariff_verified",
                  "broker_route_verified", "degiro_fee_verified",
                  "trade_ready", "order_placement_enabled"):
            self.assertFalse(out[k])

    def test_missing_venue_field_is_identified(self):
        fields = [f for f in REQUIRED_FIELDS if f != "execution_venue_mic"]
        self.assertIn("execution_venue_mic", assess(ISIN, fields)["missing_fields"])

    def test_sensitive_fields_are_not_accepted(self):
        out = assess(ISIN, ["account_number", "execution_venue_mic"])
        self.assertIn("SENSITIVE_FIELD_NAMES_DETECTED", out["blocks"])
        self.assertEqual(out["present_field_names"], [])

    def test_unknown_isin_blocks(self):
        self.assertIn("UNKNOWN_PILOT_ISIN", assess("INVALID")["blocks"])

    def test_untrusted_input_type_blocks(self):
        self.assertIn("INVALID_FIELD_NAME_INVENTORY", assess(ISIN, {"account": "secret"})["blocks"])

    def test_does_not_echo_unrecognized_fields(self):
        out = assess(ISIN, ["execution_venue_mic", "personal_note"])
        self.assertEqual(out["present_field_names"], ["execution_venue_mic"])
        self.assertNotIn("personal_note", str(out))

if __name__ == "__main__":
    unittest.main()
