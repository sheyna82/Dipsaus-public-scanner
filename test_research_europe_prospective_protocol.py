import unittest
from research_europe_prospective_protocol import register_candidate,evaluate_readiness
HASH="a"*64
def make(selected=True,day="2026-11-09",pattern="eu-recovery"):
    return register_candidate(symbol="ASML.AS",decision_day=day,pattern=pattern,
        selected=selected,decision_cutoff=day,features={"rs20":-3.2},
        source_sha256=HASH,benchmark_identity_verified=True)
class Tests(unittest.TestCase):
    def test_unverified_benchmark_blocks(self):
        with self.assertRaisesRegex(ValueError,"BENCHMARK_IDENTITY_UNVERIFIED"):
            register_candidate(symbol="A",decision_day="2026-11-09",pattern="p",
                selected=True,decision_cutoff="2026-11-09",features={"x":1},source_sha256=HASH)
    def test_lookahead_feature_blocks(self):
        with self.assertRaisesRegex(ValueError,"LOOKAHEAD_FEATURE"):
            register_candidate(symbol="A",decision_day="2026-11-09",pattern="p",
                selected=True,decision_cutoff="2026-11-09",features={"future_return":5},
                source_sha256=HASH,benchmark_identity_verified=True)
    def test_source_hash_required(self):
        with self.assertRaisesRegex(ValueError,"INVALID_SOURCE_HASH"):
            register_candidate(symbol="A",decision_day="2026-11-09",pattern="p",
                selected=True,decision_cutoff="2026-11-09",features={"x":1},
                source_sha256="fake",benchmark_identity_verified=True)
    def test_tampering_blocks(self):
        a=make();a["selected"]=False
        with self.assertRaisesRegex(ValueError,"DECISION_TAMPERED"):
            evaluate_readiness([a],start_day="2026-11-09",end_day="2027-05-09")
    def test_insufficient_sample(self):
        a=make()
        r=evaluate_readiness([a],start_day="2026-11-09",end_day="2027-05-09")
        self.assertFalse(r["minimum_observation_met"])
        self.assertFalse(r["trade_ready"])
    def test_duplicate_blocks(self):
        with self.assertRaisesRegex(ValueError,"DUPLICATE_DECISION"):
            evaluate_readiness([make(),make()],start_day="2026-11-09",end_day="2027-05-09")
if __name__=="__main__":unittest.main()
