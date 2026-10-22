import hashlib
import tempfile
import unittest
from pathlib import Path
from research_atr_local_pair_preflight import inspect_local_pair

HEADER = "Date,Open,High,Low,Close,Volume\n"
BARS = ("2026-01-05,10,11,9,10,1000\n"
        "2026-01-06,10,11,9,10.5,1100\n"
        "2026-01-07,10.5,12,10,11,1200\n")


class ATRLocalPairPreflightTests(unittest.TestCase):
    def run_pair(self, stock, benchmark, *, bad_hash=False):
        with tempfile.TemporaryDirectory() as directory:
            a, b = Path(directory) / "stock.csv", Path(directory) / "spy.csv"
            a.write_text(HEADER + stock)
            b.write_text(HEADER + benchmark)
            sha_a = hashlib.sha256(a.read_bytes()).hexdigest()
            sha_b = hashlib.sha256(b.read_bytes()).hexdigest()
            return inspect_local_pair(a, b, expected_stock_sha256="0" * 64 if bad_hash else sha_a,
                                      expected_spy_sha256=sha_b)

    def test_aligned_synthetic_pair_remains_unverified(self):
        result = self.run_pair(BARS, BARS)
        self.assertEqual(result["status"], "STRUCTURAL_REVIEW_ONLY")
        self.assertTrue(result["aligned_sessions"])
        self.assertFalse(result["trade_ready"])
        self.assertFalse(result["independent_holdout_verified"])

    def test_hash_mismatch_blocks(self):
        result = self.run_pair(BARS, BARS, bad_hash=True)
        self.assertEqual(result["reason"], "hash_mismatch")

    def test_session_mismatch_blocks(self):
        result = self.run_pair(BARS, BARS.replace("2026-01-07", "2026-01-08"))
        self.assertEqual(result["reason"], "unaligned_sessions")

    def test_suspicious_jump_blocks(self):
        result = self.run_pair(BARS.replace("10.5,12,10,11,1200", "21,22,20,21,1200"), BARS)
        self.assertEqual(result["reason"], "price_anomaly_review_required")


if __name__ == "__main__":
    unittest.main()
