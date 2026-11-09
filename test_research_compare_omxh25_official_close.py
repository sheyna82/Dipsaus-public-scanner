"""Offline tests of documented Nasdaq/Yahoo historical value crosscheck."""
import copy
import unittest
from datetime import datetime, timezone
from research_compare_omxh25_official_close import compare_omxh25_capture

def capture(close=6221.7900390625):
    return {"research_only": True, "trade_ready": False,
            "benchmark_identity_verified": False,
            "series": {"OMXH25": {
                "provider_symbol": "^OMXH25",
                "provider_metadata": {"currency": "EUR", "instrumentType": "INDEX",
                                      "exchangeName": "STO", "timezone": "CET"},
                "bars": [{"t": int(datetime(2026, 11, 6, 8, tzinfo=timezone.utc).timestamp()),
                          "close": close}]}}}

class OfficialCloseComparisonTests(unittest.TestCase):
    def test_dated_close_matches_without_identity_approval(self):
        result = compare_omxh25_capture(capture())
        self.assertEqual(result["status"], "historical_value_match_unverified_identity")
        self.assertEqual(result["compared_days"], 1)
        self.assertFalse(result["benchmark_identity_verified"])
        self.assertFalse(result["venue_mapping_explained"])
        self.assertFalse(result["official_eod_raw_bytes_verified"])
        self.assertFalse(result["trade_ready"])

    def test_reject_different_close(self):
        with self.assertRaisesRegex(ValueError, "CLOSE_CONFLICT"):
            compare_omxh25_capture(capture(6188.75))

    def test_reject_missing_date(self):
        doc = capture()
        doc["series"]["OMXH25"]["bars"] = []
        with self.assertRaisesRegex(ValueError, "PINNED_DATE_MISSING"):
            compare_omxh25_capture(doc)

    def test_reject_wrong_currency(self):
        doc = capture()
        doc["series"]["OMXH25"]["provider_metadata"]["currency"] = "USD"
        with self.assertRaisesRegex(ValueError, "METADATA_INVALID"):
            compare_omxh25_capture(doc)

    def test_reject_trade_promotion(self):
        doc = capture()
        doc["trade_ready"] = True
        with self.assertRaisesRegex(ValueError, "UNSAFE_CAPTURE_GATE"):
            compare_omxh25_capture(doc)

    def test_reject_duplicate_session(self):
        doc = capture()
        doc["series"]["OMXH25"]["bars"].append(copy.deepcopy(doc["series"]["OMXH25"]["bars"][0]))
        with self.assertRaisesRegex(ValueError, "DUPLICATE_SESSION"):
            compare_omxh25_capture(doc)

if __name__ == "__main__":
    unittest.main()
