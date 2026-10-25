import json
import tempfile
import unittest
from pathlib import Path
from research_prospective_outcome_writer import write_outcome


class OutcomeWriterTests(unittest.TestCase):
    def setUp(self):
        self.days = ["2026-10-26", "2026-10-27", "2026-10-28", "2026-10-29"]
        self.stock = [{"date": d, "close": v} for d, v in zip(self.days, [100, 98, 95, 94])]
        self.spy = [{"date": d, "close": v} for d, v in zip(self.days, [100, 101, 102, 103])]

    def test_pending_then_immutable_outcome(self):
        with tempfile.TemporaryDirectory() as tmp:
            candidate = Path(tmp) / "signal.json"
            original = json.dumps({"protocol_id": "v1", "symbol": "AMD",
                                   "signal_session": self.days[0],
                                   "future_outcome": None, "trade_ready": False})
            candidate.write_text(original)
            pending = write_outcome(candidate, self.stock[:3], self.spy[:3], tmp)
            self.assertEqual(pending["status"], "pending_three_future_sessions")
            first = write_outcome(candidate, self.stock, self.spy, tmp)
            self.assertEqual(first["status"], "created")
            self.assertTrue(first["record"]["severe_downside_event"])
            self.assertEqual(candidate.read_text(), original)
            self.assertEqual(write_outcome(candidate, self.stock, self.spy, tmp)["status"],
                             "duplicate")
            changed = [dict(x) for x in self.stock]
            changed[-1]["close"] = 99
            with self.assertRaisesRegex(ValueError, "existing_outcome_conflict"):
                write_outcome(candidate, changed, self.spy, tmp)

    def test_missing_future_stock_session(self):
        with tempfile.TemporaryDirectory() as tmp:
            candidate = Path(tmp) / "signal.json"
            candidate.write_text(json.dumps({"protocol_id": "v1", "symbol": "AMD",
                "signal_session": self.days[0], "future_outcome": None, "trade_ready": False}))
            result = write_outcome(candidate, self.stock[:-1], self.spy, tmp)
            self.assertEqual(result["status"], "missing_stock_future_session")


if __name__ == "__main__":
    unittest.main()
