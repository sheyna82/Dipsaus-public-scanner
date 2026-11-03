import unittest
from research_prospective_batch import generate_prospective_batch, audit_prospective_batch_availability


class ProspectiveBatchTests(unittest.TestCase):
    def setUp(self):
        self.days = ["2026-10-20", "2026-10-21", "2026-10-22", "2026-10-26"]
        self.spy = [{"date": day, "close": 100 + i} for i, day in enumerate(self.days)]
        self.stock = {symbol: [{"date": day, "close": 100 + 2 * i}
                      for i, day in enumerate(self.days)]
                      for symbol in ("COHU", "AMD", "META")}

    def test_complete_batch(self):
        result = generate_prospective_batch(self.stock, self.spy,
                                            signal_session="2026-10-26")
        self.assertEqual([r["status"] for r in result["results"]], ["candidate"] * 3)
        self.assertEqual(result["results"][0]["record"]["input_sessions"], self.days)
        self.assertFalse(result["trade_ready"])

    def test_missing_session_is_not_filled(self):
        self.stock["AMD"].pop(1)
        result = generate_prospective_batch(self.stock, self.spy,
                                            signal_session="2026-10-26")
        self.assertEqual(result["results"][1]["status"], "missing_stock_trading_session")

    def test_future_benchmark_rows_rejected(self):
        self.spy.append({"date": "2026-10-27", "close": 110})
        with self.assertRaisesRegex(ValueError, "future_benchmark_data_in_candidate_input"):
            generate_prospective_batch(self.stock, self.spy,
                                       signal_session="2026-10-26")

    def test_future_stock_rows_block_only_affected_symbol(self):
        self.stock["AMD"].append({"date": "2026-10-27", "close": 120})
        result = generate_prospective_batch(self.stock, self.spy,
                                            signal_session="2026-10-26")
        self.assertEqual([r["status"] for r in result["results"]],
                         ["candidate", "future_stock_data_in_candidate_input", "candidate"])

    def test_prospective_availability_audit_reuses_point_in_time_gate(self):
        batch = generate_prospective_batch(self.stock, self.spy,
                                            signal_session="2026-10-26")
        metadata = {"provider": "synthetic-test",
                    "observed_at": "2026-10-26T20:00:00+00:00",
                    "published_at": "2026-10-26T20:01:00+00:00",
                    "ingested_at": "2026-10-26T20:02:00+00:00",
                    "revision_asof": "2026-10-26T20:01:00+00:00"}
        sources = {symbol: dict(metadata) for symbol in ("COHU", "AMD", "META", "SPY")}
        result = audit_prospective_batch_availability(
            batch, sources, decision_at="2026-10-26T20:03:00+00:00")
        self.assertTrue(result["metadata_chronology_accepted"])
        self.assertFalse(result["independent_prospective_proof"])
        sources["AMD"]["ingested_at"] = "2026-10-27T20:02:00+00:00"
        result = audit_prospective_batch_availability(
            batch, sources, decision_at="2026-10-26T20:03:00+00:00")
        self.assertFalse(result["metadata_chronology_accepted"])
        self.assertIn("future_ingested_at", result["symbols"]["AMD"]["reasons"])

    def test_prospective_availability_audit_requires_full_coverage(self):
        batch = generate_prospective_batch(self.stock, self.spy,
                                            signal_session="2026-10-26")
        with self.assertRaisesRegex(ValueError, "prospective_source_coverage_mismatch"):
            audit_prospective_batch_availability(
                batch, {"SPY": {}}, decision_at="2026-10-26T20:03:00+00:00")

    def test_duplicate_session_rejected(self):
        self.spy.append(self.spy[-1].copy())
        with self.assertRaisesRegex(ValueError, "duplicate_spy_session"):
            generate_prospective_batch(self.stock, self.spy,
                                       signal_session="2026-10-26")


if __name__ == "__main__":
    unittest.main()
