import unittest
from discovery_coverage_audit import audit_us_batch,audit_eu_joined
class DiscoveryCoverageTests(unittest.TestCase):
    def test_us_cannot_claim_per_symbol_proof(self):
        r={"sample_symbols":["A","B"],"requested_symbols":2,"actual_symbols_screened":1,"failures":{"B":"TimeoutError"},"candidates":[{"symbol":"A"}]}
        a=audit_us_batch(r)
        self.assertFalse(a["complete"])
        self.assertFalse(a["per_symbol_screened_proof"])
        self.assertEqual(a["provider_failures"],1)
    def test_us_rejects_mismatched_counts(self):
        with self.assertRaises(ValueError):
            audit_us_batch({"sample_symbols":["A"],"requested_symbols":1,"actual_symbols_screened":0,"failures":{},"candidates":[]})
    def test_us_full_symbol_proof(self):
        r={"sample_symbols":["A","B"],"requested_symbols":2,"actual_symbols_screened":1,
           "screened_symbols":["A"],"failures":{"B":"TimeoutError"},"candidates":[{"symbol":"A"}]}
        a=audit_us_batch(r)
        self.assertTrue(a["complete"])
        self.assertTrue(a["per_symbol_screened_proof"])
    def test_us_missing_symbol_fails_closed(self):
        r={"sample_symbols":["A","B"],"requested_symbols":2,"actual_symbols_screened":2,
           "screened_symbols":["A"],"failures":{},"candidates":[]}
        with self.assertRaises(ValueError): audit_us_batch(r)
    def test_eu_does_not_claim_full_universe(self):
        a=audit_eu_joined({"candidates":[{"symbol":"A"}],"joined_count":1,"historical_universe":100})
        self.assertFalse(a["complete"])
        self.assertEqual(a["joined"],1)
    def test_eu_rejects_duplicates(self):
        with self.assertRaises(ValueError):
            audit_eu_joined({"candidates":[{"symbol":"A"},{"symbol":"A"}],"joined_count":2})
if __name__=="__main__": unittest.main()
