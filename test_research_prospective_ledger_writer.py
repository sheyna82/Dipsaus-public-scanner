import tempfile
import unittest
from pathlib import Path
from research_prospective_ledger_writer import write_candidate_batch


class LedgerWriterTests(unittest.TestCase):
    def batch(self):
        return {"signal_session": "2026-10-26", "results": [
            {"symbol": "AMD", "status": "candidate",
             "record": {"protocol_id": "dipsaus-prospective-momentum-v1",
                        "symbol": "AMD", "signal_session": "2026-10-26",
                        "future_outcome": None, "trade_ready": False}},
            {"symbol": "META", "status": "missing_stock_trading_session"}]}

    def test_write_repeat_and_conflict(self):
        with tempfile.TemporaryDirectory() as tmp:
            first = write_candidate_batch(self.batch(), tmp)
            self.assertEqual(len(first["created"]), 1)
            self.assertEqual(len(first["rejected"]), 1)
            second = write_candidate_batch(self.batch(), tmp)
            self.assertEqual(len(second["duplicates"]), 1)
            batch = self.batch()
            batch["results"][0]["record"]["signal_positive_past_excess"] = True
            with self.assertRaisesRegex(ValueError, "existing_candidate_conflict"):
                write_candidate_batch(batch, tmp)

    def test_unsafe_candidate_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            batch = self.batch()
            batch["results"][0]["record"]["future_outcome"] = 12
            with self.assertRaisesRegex(ValueError, "unsafe_candidate"):
                write_candidate_batch(batch, tmp)
            self.assertEqual(list(Path(tmp).iterdir()), [])


if __name__ == "__main__":
    unittest.main()
