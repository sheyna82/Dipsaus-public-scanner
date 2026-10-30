import unittest
from research_swing_international_candidates import international_candidate_manifest
class InternationalCandidatesTests(unittest.TestCase):
    def test_no_candidate_claims_broker_verification(self):
        result = international_candidate_manifest()
        self.assertGreaterEqual(result["countries"], 20)
        self.assertGreaterEqual(result["candidate_count"], 100)
        self.assertEqual(result["broker_verified_count"], 0)
        self.assertTrue(all(not r["live_alert_eligible"] for r in result["candidates"]))
    def test_unique_research_symbols(self):
        rows = international_candidate_manifest()["candidates"]
        self.assertEqual(len(rows), len(set(x["research_symbol"] for x in rows)))
if __name__ == "__main__":
    unittest.main()
