"""Replay wrapper tests use synthetic bytes and a synthetic pinned digest."""
import hashlib
import unittest
from datetime import date
from unittest.mock import patch
from research_iso_replay import replay

CSV = (b'MIC,OPERATING MIC,OPRT/SGMT,STATUS,MARKET NAME-INSTITUTION DESCRIPTION,CREATION DATE,LAST UPDATE DATE,EXPIRY DATE\n'
       b'XETR,XETR,OPRT,ACTIVE,Xetra,20050627,20161128,\n'
       b'XETA,XETR,SGMT,ACTIVE,Regulated,20080324,20161128,\n'
       b'XETB,XETR,SGMT,ACTIVE,Freiverkehr,20080324,20251222,\n'
       b'XAMS,XAMS,OPRT,ACTIVE,Amsterdam,20050627,20150427,\n'
       b'XHEL,XHEL,OPRT,ACTIVE,Helsinki,20110124,20230925,\n')

class ReplayTests(unittest.TestCase):
    def check(self, raw=CSV, as_of=date(2026, 11, 23)):
        with patch("research_iso_replay.PINNED_SHA256", hashlib.sha256(CSV).hexdigest()):
            return replay(raw, as_of=as_of)
    def test_pinned_fixture_consistent_after_effective_date(self):
        result = self.check()
        self.assertEqual(result["status"], "OFFLINE_ISO_MIC_RECORDS_CONSISTENT")
        self.assertEqual(len(result["selected"]), 5)
        self.assertFalse(result["trade_ready"])
    def test_before_effective_date_blocked(self):
        self.assertEqual(self.check(as_of=date(2026, 11, 19))["reason"], "NOT_YET_EFFECTIVE")
    def test_tampered_file_blocked(self):
        self.assertEqual(self.check(CSV+b"\n")["reason"], "DIGEST_MISMATCH")

if __name__ == "__main__":
    unittest.main()
