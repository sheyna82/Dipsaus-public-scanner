"""Coverage gate must never turn observations into trading evidence."""
import unittest
from research_finnhub_observation_coverage import assess_observation_coverage

class CoverageTests(unittest.TestCase):
    def collection(self, n=1, days=1):
        obs=[{"symbol":"AMD","request_started_utc":f"2026-11-{3+i%days:02d}T20:00:00+00:00","trade_ready":False} for i in range(n)]
        return {"schema":"dipsaus_research_artifact_collection_v1",
                "observations":obs,"count":len(obs),
                "quote_accuracy_verified":False,"prospective_signal_proven":False,
                "trade_ready":False}
    def test_one_observation_insufficient(self):
        x=assess_observation_coverage(self.collection())
        self.assertFalse(x["coverage_thresholds_met"])
        self.assertIn("INSUFFICIENT_DISTINCT_DAYS",x["blocking_reasons"])
    def test_many_same_day_insufficient(self):
        x=assess_observation_coverage(self.collection(30,1))
        self.assertFalse(x["coverage_thresholds_met"])
    def test_threshold_met_still_not_trade_ready(self):
        x=assess_observation_coverage(self.collection(20,5))
        self.assertTrue(x["coverage_thresholds_met"])
        self.assertFalse(x["trade_ready"])
        self.assertFalse(x["prospective_edge_proven"])
    def test_invalid_collection_claim_rejected(self):
        c=self.collection()
        c["trade_ready"]=True
        with self.assertRaisesRegex(ValueError,"unsafe_collection_claim"):
            assess_observation_coverage(c)
    def test_invalid_timestamp_rejected(self):
        c=self.collection()
        c["observations"][0]["request_started_utc"]="2026-11-03T20:00:00"
        with self.assertRaisesRegex(ValueError,"invalid_timestamp"):
            assess_observation_coverage(c)
    def test_count_mismatch_rejected(self):
        c=self.collection()
        c["count"]=5
        with self.assertRaisesRegex(ValueError,"invalid_collection_count"):
            assess_observation_coverage(c)

if __name__=="__main__": unittest.main()
