import unittest
from research.spoor2_iso_mic_candidate_match_20261113 import inspect_mic_candidates


class IsoMicCandidateMatchTests(unittest.TestCase):
    def test_three_unique_candidates_still_unattested(self):
        r = inspect_mic_candidates(b"MIC,COUNTRY\nXAMS,NL\nXETR,DE\nXHEL,FI\n")
        self.assertEqual([r["candidate_matches"][m]["count"] for m in
                          ("XAMS", "XETR", "XHEL")], [1, 1, 1])
        self.assertFalse(r["mic_registered"])
        self.assertFalse(r["source_attested"])
        self.assertFalse(r["trade_ready"])

    def test_missing_mic_is_blocked(self):
        r = inspect_mic_candidates(b"MIC,COUNTRY\nXAMS,NL\n")
        self.assertIn("MISSING_OR_DUPLICATE_MIC_XETR", r["blocks"])

    def test_duplicate_mic_is_blocked(self):
        r = inspect_mic_candidates(b"MIC,COUNTRY\nXAMS,NL\nXAMS,NL\nXETR,DE\nXHEL,FI\n")
        self.assertIn("MISSING_OR_DUPLICATE_MIC_XAMS", r["blocks"])

    def test_invalid_csv_is_blocked(self):
        r = inspect_mic_candidates(b"not,csv\n")
        self.assertIn("CSV_INTAKE_REJECTED", r["blocks"])

    def test_missing_mic_column_is_blocked(self):
        r = inspect_mic_candidates(b"CODE,COUNTRY\nXAMS,NL\n")
        self.assertIn("MIC_COLUMN_NOT_FOUND", r["blocks"])

    def test_case_sensitive_no_normalization(self):
        r = inspect_mic_candidates(b"MIC,COUNTRY\nxams,NL\nXETR,DE\nXHEL,FI\n")
        self.assertEqual(r["candidate_matches"]["XAMS"]["count"], 0)

    def test_custom_column(self):
        r = inspect_mic_candidates(
            b"MIC_CODE,COUNTRY\nXAMS,NL\nXETR,DE\nXHEL,FI\n",
            mic_column="MIC_CODE")
        self.assertEqual(r["candidate_matches"]["XAMS"]["count"], 1)

    def test_never_verifies_broker_fee(self):
        r = inspect_mic_candidates(b"MIC\nXAMS\nXETR\nXHEL\n")
        self.assertFalse(r["degiro_fee_verified"])
        self.assertFalse(r["order_placement_enabled"])
