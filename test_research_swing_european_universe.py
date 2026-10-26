import unittest
from research_swing_european_universe import european_manifest,audit_european_coverage
class EuropeanUniverseTests(unittest.TestCase):
 def test_manifest(self):
  m=european_manifest()
  self.assertEqual(len(m["symbols"]),20)
  self.assertEqual(len({x["sector"] for x in m["symbols"]}),10)
  self.assertTrue(all(x["currency"]=="EUR" for x in m["symbols"]))
 def test_missing_coverage(self):
  m=european_manifest()
  s={x["symbol"]:"normalized_unverified" for x in m["symbols"]+m["benchmarks"]}
  s["ASML.AS"]="unavailable"
  self.assertEqual(audit_european_coverage(s)["unavailable"],["ASML.AS"])
  del s["SAN.MC"]
  with self.assertRaises(ValueError): audit_european_coverage(s)
if __name__=="__main__": unittest.main()
