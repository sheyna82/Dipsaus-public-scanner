"""Synthetic integration tests: ISO venue MIC is not a Xetra segment code."""
import unittest
from datetime import date
from research_eu_crosswalk import correlate

X = {"status": "OFFLINE_XETRA_SNAPSHOT_CONSISTENT", "instruments": {
    "DE0006231004": {"mic": "XETR", "segment": "045",
                     "segment_description": "Prime Standard", "research_active": True}}}
I = {"status": "OFFLINE_ISO_MIC_RECORDS_CONSISTENT",
     "effective_date": "2026-11-23",
     "selected": {"XETR": {"kind": "OPRT", "operating_mic": "XETR", "status": "ACTIVE"}}}

class CrosswalkTests(unittest.TestCase):
    def test_consistent_but_never_trade_ready(self):
        r = correlate(X, I, as_of=date(2026, 11, 23))
        self.assertEqual(r["status"], "OFFLINE_EU_CROSSWALK_CONSISTENT")
        self.assertEqual(r["instruments"]["DE0006231004"]["xetra_segment_code"], "045")
        self.assertFalse(r["instruments"]["DE0006231004"]["iso_segment_mic_verified"])
        self.assertFalse(r["trade_ready"])
        self.assertFalse(r["order_placement_enabled"])
    def test_pre_effective_blocked(self):
        self.assertEqual(correlate(X, I, as_of=date(2026, 11, 19))["reason"], "ISO_NOT_YET_EFFECTIVE")
    def test_unvalidated_iso_blocked(self):
        self.assertEqual(correlate(X, {}, as_of=date(2026, 11, 23))["reason"], "UNVALIDATED_ISO")
    def test_unvalidated_xetra_blocked(self):
        self.assertEqual(correlate({}, I, as_of=date(2026, 11, 23))["reason"], "UNVALIDATED_XETRA")
    def test_inactive_instrument_blocked(self):
        x = {**X, "instruments": {"a": {**X["instruments"]["DE0006231004"], "research_active": False}}}
        self.assertEqual(correlate(x, I, as_of=date(2026, 11, 23))["reason"], "INACTIVE_INSTRUMENT")
    def test_wrong_mic_blocked(self):
        x = {**X, "instruments": {"a": {**X["instruments"]["DE0006231004"], "mic": "XAMS"}}}
        self.assertEqual(correlate(x, I, as_of=date(2026, 11, 23))["reason"], "VENUE_MIC_NOT_CORROBORATED")
    def test_invalid_date_blocked(self):
        self.assertEqual(correlate(X, I, as_of="2026-11-23")["reason"], "INVALID_AS_OF")
    def test_missing_segment_blocked(self):
        x = {**X, "instruments": {"a": {**X["instruments"]["DE0006231004"], "segment_description": ""}}}
        self.assertEqual(correlate(x, I, as_of=date(2026, 11, 23))["reason"], "UNVERIFIED_XETRA_SEGMENT")

if __name__ == "__main__":
    unittest.main()
