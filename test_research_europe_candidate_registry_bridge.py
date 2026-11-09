import unittest
from research_europe_candidate_registry_bridge import register_snapshot
BASE={"symbol":"ASML.AS","decision_day":"2026-11-09","as_of_complete_day":"2026-11-09",
      "pattern":"eu-recovery","selected":False,"features":{"rs20":-5.0},
      "source_sha256":"a"*64,"research_only":True,"trade_ready":False}
class Tests(unittest.TestCase):
    def test_identity_unverified_blocks(self):
        with self.assertRaisesRegex(ValueError,"BENCHMARK_IDENTITY_UNVERIFIED"):
            register_snapshot(BASE,decision_cutoff="2026-11-09")
    def test_valid_research_snapshot(self):
        r=register_snapshot(BASE,decision_cutoff="2026-11-09",benchmark_identity_verified=True)
        self.assertFalse(r["selected"])
        self.assertFalse(r["trade_ready"])
        self.assertEqual(len(r["decision_sha256"]),64)
    def test_lookahead_snapshot_blocks(self):
        with self.assertRaisesRegex(ValueError,"LOOKAHEAD_SNAPSHOT"):
            register_snapshot({**BASE,"forward_return":3.0},decision_cutoff="2026-11-09",benchmark_identity_verified=True)
    def test_mismatched_day_blocks(self):
        with self.assertRaisesRegex(ValueError,"SNAPSHOT_DAY_MISMATCH"):
            register_snapshot({**BASE,"as_of_complete_day":"2026-11-06"},decision_cutoff="2026-11-09",benchmark_identity_verified=True)
    def test_live_snapshot_blocks(self):
        with self.assertRaisesRegex(ValueError,"NOT_ISOLATED_RESEARCH"):
            register_snapshot({**BASE,"trade_ready":True},decision_cutoff="2026-11-09",benchmark_identity_verified=True)
    def test_missing_fields_blocks(self):
        with self.assertRaisesRegex(ValueError,"MISSING_SNAPSHOT_FIELDS"):
            register_snapshot({"symbol":"ASML.AS"},decision_cutoff="2026-11-09")
if __name__=="__main__":unittest.main()
