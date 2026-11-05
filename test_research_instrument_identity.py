import unittest
from research_instrument_identity import assess_instrument_identity


class InstrumentIdentityTests(unittest.TestCase):
    def test_matching_metadata_does_not_prove_authenticated_identity(self):
        a = {"isin": "NL0012817175", "mic": "XAMS", "currency": "EUR", "instrument_type": "EQUITY"}
        result = assess_instrument_identity(a, dict(a))
        self.assertEqual(result["status"], "METADATA_MATCH_UNAUTHENTICATED")
        self.assertFalse(result["identity_verified"])
        self.assertFalse(result["automatic_merge_allowed"])
        self.assertFalse(result["trade_ready"])

    def test_conflicting_exchange_blocks_match(self):
        a = {"isin": "NL0012817175", "mic": "XAMS", "currency": "EUR", "instrument_type": "EQUITY"}
        b = dict(a, mic="XETR")
        result = assess_instrument_identity(a, b)
        self.assertEqual(result["status"], "CONFLICT_REQUIRES_REVIEW")
        self.assertEqual(result["conflicting_fields"], ["mic"])

    def test_missing_metadata_is_not_identity_proof(self):
        result = assess_instrument_identity({"isin": "NL0012817175"}, {"isin": "NL0012817175"})
        self.assertEqual(result["status"], "INSUFFICIENT_IDENTITY_EVIDENCE")
        self.assertFalse(result["automatic_merge_allowed"])

    def test_invalid_fields_fail_closed(self):
        for record in (None, {"isin": ""}, {"mic": 12}, {"currency": True}):
            with self.subTest(record=record):
                with self.assertRaises(ValueError):
                    assess_instrument_identity(record, {})

    def test_case_normalization_does_not_override_missing_authentication(self):
        a = {"isin": " nl0012817175 ", "mic": "xams", "currency": "eur", "instrument_type": "equity"}
        b = {"isin": "NL0012817175", "mic": "XAMS", "currency": "EUR", "instrument_type": "EQUITY"}
        self.assertTrue(assess_instrument_identity(a, b)["metadata_matches"])
        self.assertFalse(assess_instrument_identity(a, b)["source_authenticated"])


if __name__ == "__main__":
    unittest.main()
