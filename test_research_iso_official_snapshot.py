"""Synthetic ISO MIC tests; not a substitute for the official CSV."""
import hashlib
import unittest
from datetime import date
from research_iso_official_snapshot import inspect_official_mic_csv

CSV = (b'MIC,OPERATING MIC,OPRT/SGMT,STATUS,MARKET NAME-INSTITUTION DESCRIPTION,CREATION DATE,LAST UPDATE DATE,EXPIRY DATE\n'
       b'XETR,XETR,OPRT,ACTIVE,Xetra,20050627,20161128,\nXETA,XETR,SGMT,ACTIVE,Regulated,20080324,20161128,\n')

class OfficialMicTests(unittest.TestCase):
    def check(self, raw=CSV, **kw):
        args = dict(expected_sha256=hashlib.sha256(raw).hexdigest(),
                    publication_date=date(2026, 11, 9), effective_date=date(2026, 11, 23),
                    as_of=date(2026, 11, 24), requested_mics=("XETR", "XETA"))
        args.update(kw)
        return inspect_official_mic_csv(raw, **args)
    def test_valid(self):
        r = self.check()
        self.assertEqual(r["record_count"], 2)
        self.assertFalse(r["trade_ready"])
    def test_pre_effective(self):
        self.assertEqual(self.check(as_of=date(2026, 11, 19))["reason"], "NOT_YET_EFFECTIVE")
    def test_hash(self):
        self.assertEqual(self.check(expected_sha256="0"*64)["reason"], "DIGEST_MISMATCH")
    def test_missing_mic(self):
        self.assertEqual(self.check(requested_mics=("XAMS",))["reason"], "MISSING_MIC")
    def test_inactive(self):
        raw = CSV.replace(b'XETA,XETR,SGMT,ACTIVE', b'XETA,XETR,SGMT,EXPIRED')
        self.assertEqual(self.check(raw)["reason"], "INACTIVE_OR_INVALID_PARENT")
    def test_duplicate(self):
        self.assertEqual(self.check(CSV+b'XETR,XETR,OPRT,ACTIVE,Xetra,20050627,20161128,\n')["reason"], "DUPLICATE_MIC")
    def test_bad_parent(self):
        raw = CSV.replace(b'XETA,XETR,SGMT', b'XETA,XXXX,SGMT')
        self.assertEqual(self.check(raw)["reason"], "INACTIVE_OR_INVALID_PARENT")
    def test_operating_mismatch(self):
        raw = CSV.replace(b'XETR,XETR,OPRT', b'XETR,XAMS,OPRT')
        self.assertEqual(self.check(raw)["reason"], "OPERATING_MIC_SELF_MISMATCH")
    def test_missing_header(self):
        raw = CSV.replace(b'OPERATING MIC', b'OTHER')
        self.assertEqual(self.check(raw)["reason"], "HEADER_MISMATCH")
    def test_invalid_shape(self):
        self.assertEqual(self.check(CSV+b'XETB,XETR,SGMT\n')["reason"], "ROW_SHAPE_MISMATCH")
    def test_future_updated_record_blocked(self):
        raw = CSV.replace(b"20161128", b"20270101", 1)
        self.assertEqual(self.check(raw)["reason"], "DATE_INCONSISTENCY")
    def test_expired_selected_mic_blocked(self):
        raw = CSV.replace(b"Regulated,20080324,20161128,", b"Regulated,20080324,20161128,20260101")
        self.assertEqual(self.check(raw)["reason"], "DATE_INCONSISTENCY")
    def test_invalid_creation_date_blocked(self):
        raw = CSV.replace(b"20080324", b"20081324")
        self.assertEqual(self.check(raw)["reason"], "INVALID_REGISTER_DATE")
    def test_invalid_selection(self):
        self.assertEqual(self.check(requested_mics=("bad!",))["reason"], "INVALID_SELECTION")

if __name__ == "__main__":
    unittest.main()
