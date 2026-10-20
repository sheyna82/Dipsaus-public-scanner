import unittest
from discovery_coverage_audit import audit_us_batch,audit_eu_joined,audit_eu_pipeline
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
        self.assertFalse(a["all_data_available"])
    def test_us_no_failures_means_all_data_available(self):
        r={"sample_symbols":["A"],"requested_symbols":1,"actual_symbols_screened":1,
           "screened_symbols":["A"],"failures":{},"candidates":[]}
        a=audit_us_batch(r)
        self.assertTrue(a["complete"])
        self.assertTrue(a["all_data_available"])

    def test_us_missing_symbol_fails_closed(self):
        r={"sample_symbols":["A","B"],"requested_symbols":2,"actual_symbols_screened":2,
           "screened_symbols":["A"],"failures":{},"candidates":[]}
        with self.assertRaises(ValueError): audit_us_batch(r)
    def eu_reports(self):
        h={"candidates":[{"symbol":"A","discovery_eligible":True},
                         {"symbol":"B","discovery_eligible":True},
                         {"symbol":"C","discovery_eligible":False}]}
        i={"candidates":[{"symbol":"A"},{"symbol":"B"}],
           "watchlist_eligible_count":2,"checked_count":2}
        q={"candidates":[{"symbol":"A"},{"symbol":"B"}],"checked":2}
        j={"candidates":[{"symbol":"A"},{"symbol":"B"}],"joined_count":2}
        return h,i,q,j

    def test_us_rejects_blank_symbol(self):
        r={"sample_symbols":[""],"requested_symbols":1,"actual_symbols_screened":1,
           "screened_symbols":[""],"failures":{},"candidates":[]}
        with self.assertRaises(ValueError): audit_us_batch(r)

    def test_us_rejects_invalid_batch_index(self):
        r={"sample_symbols":["A"],"requested_symbols":1,"actual_symbols_screened":1,
           "screened_symbols":["A"],"failures":{},"candidates":[],"batch_index":22}
        with self.assertRaises(ValueError): audit_us_batch(r)

    def test_eu_all_four_stages_complete(self):
        self.assertTrue(audit_eu_pipeline(*self.eu_reports())["complete"])

    def test_eu_missing_intraday_detected(self):
        h,i,q,j=self.eu_reports()
        i["candidates"].pop();i["checked_count"]=1
        q["candidates"].pop();q["checked"]=1
        j["candidates"].pop();j["joined_count"]=1
        a=audit_eu_pipeline(h,i,q,j)
        self.assertFalse(a["complete"])
        self.assertEqual(a["missing_intraday"],1)

    def test_eu_missing_quote_detected(self):
        h,i,q,j=self.eu_reports()
        q["candidates"].pop();q["checked"]=1
        a=audit_eu_pipeline(h,i,q,j)
        self.assertFalse(a["complete"])
        self.assertEqual(a["missing_quote"],1)

    def test_eu_missing_join_detected(self):
        h,i,q,j=self.eu_reports()
        j["candidates"].pop();j["joined_count"]=1
        a=audit_eu_pipeline(h,i,q,j)
        self.assertFalse(a["complete"])
        self.assertEqual(a["missing_joined"],1)

    def test_eu_rejects_duplicate_stage_symbol(self):
        h,i,q,j=self.eu_reports()
        q["candidates"].append({"symbol":"A"});q["checked"]=3
        with self.assertRaises(ValueError):
            audit_eu_pipeline(h,i,q,j)

    def test_eu_does_not_claim_full_universe(self):
        a=audit_eu_joined({"candidates":[{"symbol":"A"}],"joined_count":1,"historical_universe":100})
        self.assertFalse(a["complete"])
        self.assertEqual(a["joined"],1)
    def test_eu_rejects_duplicates(self):
        with self.assertRaises(ValueError):
            audit_eu_joined({"candidates":[{"symbol":"A"},{"symbol":"A"}],"joined_count":2})
if __name__=="__main__": unittest.main()
