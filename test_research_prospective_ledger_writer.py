import tempfile
import unittest
from pathlib import Path
from research_prospective_ledger_writer import write_candidate_batch, write_audited_candidate_batch


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

    def test_future_outcome_availability_cannot_be_predeclared(self):
        with tempfile.TemporaryDirectory() as tmp:
            batch = self.batch()
            batch["results"][0]["record"]["future_outcome_available"] = True
            with self.assertRaisesRegex(ValueError, "unsafe_candidate"):
                write_candidate_batch(batch, tmp)
            self.assertEqual(list(Path(tmp).iterdir()), [])

    def test_invalid_later_candidate_does_not_write_earlier_candidate(self):
        with tempfile.TemporaryDirectory() as tmp:
            batch = self.batch()
            batch["results"].append({"symbol": "COHU", "status": "candidate",
                                     "record": {"symbol": "COHU", "signal_session": "2026-10-26",
                                                "future_outcome": 1, "trade_ready": False}})
            with self.assertRaisesRegex(ValueError, "unsafe_candidate"):
                write_candidate_batch(batch, tmp)
            self.assertEqual(list(Path(tmp).iterdir()), [])

    def test_later_existing_conflict_does_not_write_earlier_candidate(self):
        with tempfile.TemporaryDirectory() as tmp:
            batch = self.batch()
            batch["results"].insert(0, {"symbol": "COHU", "status": "candidate",
                "record": {"protocol_id": "dipsaus-prospective-momentum-v1",
                           "symbol": "COHU", "signal_session": "2026-10-26",
                           "future_outcome": None, "trade_ready": False}})
            existing = Path(tmp) / "dipsaus-prospective-momentum-v1-AMD-2026-10-26.json"
            existing.write_text('{"different": true}\\n')
            with self.assertRaisesRegex(ValueError, "existing_candidate_conflict"):
                write_candidate_batch(batch, tmp)
            self.assertEqual(sorted(p.name for p in Path(tmp).iterdir()), [existing.name])

    def test_duplicate_identity_does_not_create_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            batch = self.batch()
            batch["results"].append(dict(batch["results"][0]))
            with self.assertRaisesRegex(ValueError, "duplicate_candidate_identity_in_batch"):
                write_candidate_batch(batch, tmp)
            self.assertEqual(list(Path(tmp).iterdir()), [])

    def source_records(self):
        metadata = {"provider": "synthetic-test",
                    "observed_at": "2026-10-26T20:00:00+00:00",
                    "published_at": "2026-10-26T20:01:00+00:00",
                    "ingested_at": "2026-10-26T20:02:00+00:00",
                    "revision_asof": "2026-10-26T20:01:00+00:00"}
        return {"AMD": dict(metadata), "SPY": dict(metadata)}

    def test_audited_writer_accepts_complete_synthetic_chronology(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = write_audited_candidate_batch(
                self.batch(), tmp, self.source_records(),
                decision_at="2026-10-26T20:03:00+00:00")
            self.assertEqual(len(result["created"]), 1)
            self.assertTrue(result["source_chronology_audit"]["metadata_chronology_accepted"])
            self.assertFalse(result["independent_prospective_proof"])

    def test_audited_writer_blocks_late_ingestion_before_write(self):
        with tempfile.TemporaryDirectory() as tmp:
            sources = self.source_records()
            sources["AMD"]["ingested_at"] = "2026-10-27T20:02:00+00:00"
            with self.assertRaisesRegex(ValueError, "prospective_source_chronology_blocked"):
                write_audited_candidate_batch(self.batch(), tmp, sources,
                    decision_at="2026-10-26T20:03:00+00:00")
            self.assertEqual(list(Path(tmp).iterdir()), [])

    def test_audited_writer_blocks_missing_source_before_write(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError, "prospective_source_coverage_mismatch"):
                write_audited_candidate_batch(self.batch(), tmp, {"AMD": self.source_records()["AMD"]},
                    decision_at="2026-10-26T20:03:00+00:00")
            self.assertEqual(list(Path(tmp).iterdir()), [])

    def test_unsafe_candidate_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            batch = self.batch()
            batch["results"][0]["record"]["future_outcome"] = 12
            with self.assertRaisesRegex(ValueError, "unsafe_candidate"):
                write_candidate_batch(batch, tmp)
            self.assertEqual(list(Path(tmp).iterdir()), [])


if __name__ == "__main__":
    unittest.main()
