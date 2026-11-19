"""Offline MIC crosswalk guard tests."""
import unittest
from research_mic_crosswalk import resolve_mic_relationship


class CrosswalkTests(unittest.TestCase):
    def setUp(self):
        self.register = {"status": "OFFLINE_MIC_SCHEMA_VALIDATED", "records": {
            "XETR": {"mic": "XETR", "kind": "OPRT", "status": "ACTIVE", "operating_mic": ""},
            "XETA": {"mic": "XETA", "kind": "SGMT", "status": "ACTIVE", "operating_mic": "XETR"},
            "XAMS": {"mic": "XAMS", "kind": "OPRT", "status": "ACTIVE", "operating_mic": ""}}}

    def check(self, **kw):
        return resolve_mic_relationship(self.register, operating_mic=kw.get("operating_mic", "XETR"),
                                        segment_mic=kw.get("segment_mic", "XETA"))

    def test_consistent_not_executable(self):
        result = self.check()
        self.assertEqual(result["status"], "OFFLINE_MIC_RELATIONSHIP_CONSISTENT")
        self.assertFalse(result["trade_ready"])
        self.assertFalse(result["broker_route_verified"])
        self.assertFalse(result["instrument_listing_verified"])

    def test_unvalidated_register(self):
        self.register["status"] = "UNVERIFIED"
        self.assertEqual(self.check()["reason"], "UNVALIDATED_REGISTER")

    def test_missing_operating_mic(self):
        self.assertEqual(self.check(operating_mic="XXXX")["reason"], "OPERATING_MIC_NOT_ACTIVE")

    def test_missing_segment(self):
        self.assertEqual(self.check(segment_mic="XXXX")["reason"], "SEGMENT_MIC_NOT_ACTIVE")

    def test_wrong_parent(self):
        self.register["records"]["XETA"]["operating_mic"] = "XAMS"
        self.assertEqual(self.check()["reason"], "SEGMENT_PARENT_MISMATCH")

    def test_inactive_segment(self):
        self.register["records"]["XETA"]["status"] = "INACTIVE"
        self.assertEqual(self.check()["reason"], "SEGMENT_MIC_NOT_ACTIVE")

    def test_inactive_parent(self):
        self.register["records"]["XETR"]["status"] = "INACTIVE"
        self.assertEqual(self.check()["reason"], "OPERATING_MIC_NOT_ACTIVE")

    def test_invalid_mic(self):
        self.assertEqual(self.check(segment_mic="XETRA")["reason"], "INVALID_MIC")

    def test_segment_cannot_be_operating(self):
        self.assertEqual(self.check(operating_mic="XETA")["reason"], "OPERATING_MIC_NOT_ACTIVE")

    def test_operating_cannot_be_segment(self):
        self.assertEqual(self.check(segment_mic="XAMS")["reason"], "SEGMENT_MIC_NOT_ACTIVE")


if __name__ == "__main__":
    unittest.main()
