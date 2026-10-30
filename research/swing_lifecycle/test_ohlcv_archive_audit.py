"""Synthetic read-only archive audit regressions."""
import gzip
import json
import math
import tempfile
import unittest
from pathlib import Path
from ohlcv_archive_audit import audit_archive

class ArchiveAuditTests(unittest.TestCase):
    def make_archive(self,rows):
        folder=tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        path=Path(folder.name)/"archive.jsonl.gz"
        with gzip.open(path,"wt",encoding="utf-8") as handle:
            for row in rows:handle.write(json.dumps(row)+"\n")
        return path
    def test_valid_archive(self):
        p=self.make_archive([{"symbol":"ABC","bars":[["2026-01-02",10,12,9,11,100],["2026-01-05",11,13,10,12,200]]}])
        result=audit_archive(p)
        self.assertEqual(result["unique_symbols"],1)
        self.assertEqual(result["valid_bars"],2)
        self.assertEqual(result["first_session"],"2026-01-02")
        self.assertEqual(result["issues"],{})
    def test_duplicate_and_nonchronological(self):
        p=self.make_archive([{"symbol":"ABC","bars":[["2026-01-05",10,12,9,11,100],["2026-01-05",10,12,9,11,100],["2026-01-02",10,12,9,11,100]]},{"symbol":"ABC","bars":[]}])
        issues=audit_archive(p)["issues"]
        self.assertEqual(issues["DUPLICATE_SYMBOL_RECORD"],1)
        self.assertEqual(issues["DUPLICATE_SESSION"],1)
        self.assertEqual(issues["NONINCREASING_SESSION"],2)
    def test_nonfinite_bar_rejected(self):
        p=self.make_archive([{"symbol":"ABC","bars":[["2026-01-05",10,12,9,math.nan,100]]}])
        self.assertEqual(audit_archive(p)["issues"]["INVALID_BAR"],1)
    def test_invalid_bar(self):
        p=self.make_archive([{"symbol":"ABC","bars":[["2026-01-05",10,8,9,11,100]]}])
        self.assertEqual(audit_archive(p)["issues"]["INVALID_BAR"],1)
if __name__=="__main__":unittest.main()
