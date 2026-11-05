import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from research_swing_regime_archive_ab import run_regime_ab_archive

class ArchiveABTests(unittest.TestCase):
    def make_zip(self, path, *, shifted=False):
        symbols = ["AAA","BBB","CCC","DDD","EEE","FFF"]
        with zipfile.ZipFile(path,"w") as z:
            z.writestr("coverage.json",json.dumps({"manifest":{"symbols":[{"symbol":s} for s in symbols]}}))
            for s in symbols+["SPY"]:
                rows=[{"timestamp":i*86400+(1 if shifted and s=="SPY" else 0),
                       "open":100+i*.1,"high":101+i*.1,"low":99+i*.1,
                       "close":100+i*.1,"volume":1000} for i in range(105)]
                z.writestr(s+".json",json.dumps({"rows":rows}))
    def test_runs_all_three_horizons(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"prices.zip"
            self.make_zip(path)
            r=run_regime_ab_archive(path)
            self.assertEqual([x["horizon"] for x in r["summary"]],[5,10,15])
            self.assertFalse(r["edge_proven"])
    def test_rejects_unaligned_dates(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"prices.zip"
            self.make_zip(path,shifted=True)
            with self.assertRaises(ValueError):
                run_regime_ab_archive(path)
if __name__=="__main__":
    unittest.main()
