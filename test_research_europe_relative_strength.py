"""Offline fail-closed EU comparison tests."""
import unittest
from research_europe_relative_strength import compare
class Tests(unittest.TestCase):
    def test_missing_evidence_blocks(self):
        with self.assertRaisesRegex(ValueError,"BENCHMARK_IDENTITY_UNVERIFIED"):
            compare({"trade_ready":False},{"trade_ready":False},{})
    def test_partial_evidence_blocks(self):
        with self.assertRaisesRegex(ValueError,"BENCHMARK_IDENTITY_UNVERIFIED"):
            compare({"trade_ready":False},{"trade_ready":False},{"AEX":True})
    def test_trade_ready_source_blocks(self):
        with self.assertRaisesRegex(ValueError,"RESEARCH_ONLY_REQUIRED"):
            compare({"trade_ready":True},{"trade_ready":False},{})
if __name__=="__main__":unittest.main()
