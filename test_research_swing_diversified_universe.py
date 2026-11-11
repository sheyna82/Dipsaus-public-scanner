import unittest
from research_swing_diversified_universe import universe_manifest,audit_coverage

class TestUniverse(unittest.TestCase):
    def test_balanced_manifest(self):
        m=universe_manifest()
        self.assertEqual(len(m["symbols"]),18)
        self.assertEqual(len(set(x["sector"] for x in m["symbols"])),9)
        self.assertEqual(len(m["benchmarks"]),2)
    def test_missing_data_not_silently_excluded(self):
        m=universe_manifest()
        status={x["symbol"]:"normalized_unverified" for x in m["symbols"]}
        status.update({"SPY":"normalized_unverified","IWM":"http_error"})
        result=audit_coverage(status)
        self.assertEqual(result["unavailable"],["IWM"])
        del status["PFE"]
        with self.assertRaises(ValueError):
            audit_coverage(status)

if __name__=="__main__":
    unittest.main()
