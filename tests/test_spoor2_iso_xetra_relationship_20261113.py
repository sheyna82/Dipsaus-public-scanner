import unittest
from research.spoor2_iso_xetra_relationship_20261113 import audit_xetra_iso_relationship

def row(mic, kind, category, name):
    return {"MIC": mic, "OPERATING MIC": "XETR", "OPRT/SGMT": kind,
            "STATUS": "ACTIVE", "ISO COUNTRY CODE (ISO 3166)": "DE",
            "CREATION DATE": "20080324", "EXPIRY DATE": "",
            "MARKET CATEGORY CODE": category,
            "MARKET NAME-INSTITUTION DESCRIPTION": name}

class IsoRelationshipTests(unittest.TestCase):
    def test_unique_iso_relationship_stays_non_tradable(self):
        data = {"target_rows": [row("XETR", "OPRT", "NSPD", "XETRA"),
                                row("XETA", "SGMT", "RMKT", "XETRA - REGULIERTER MARKT")]}
        result = audit_xetra_iso_relationship(data)
        self.assertEqual(result["iso_regulated_segment_candidate"], "XETA")
        self.assertTrue(result["iso_operating_mic_found"])
        self.assertFalse(result["segment_mic_verified"])
        self.assertFalse(result["trade_ready"])

    def test_duplicate_xeta_rejected(self):
        x = row("XETA", "SGMT", "RMKT", "XETRA - REGULIERTER MARKT")
        result = audit_xetra_iso_relationship({"target_rows": [x, x]})
        self.assertIsNone(result["iso_regulated_segment_candidate"])

    def test_expired_xeta_rejected(self):
        x = row("XETA", "SGMT", "RMKT", "XETRA - REGULIERTER MARKT")
        x["EXPIRY DATE"] = "20190826"
        result = audit_xetra_iso_relationship({"target_rows": [x]})
        self.assertIsNone(result["iso_regulated_segment_candidate"])

if __name__ == "__main__":
    unittest.main()
