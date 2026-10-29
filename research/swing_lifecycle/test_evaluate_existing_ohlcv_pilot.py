import gzip
import json
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path
from research.swing_lifecycle.evaluate_existing_ohlcv_pilot import evaluate_pilot_artifact


class ExistingOhlcvPilotTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "pilot.jsonl.gz"

    def write_fixture(self, length=240):
        start = date(2025, 1, 1)
        bars = []
        for i in range(length):
            day = (start + timedelta(days=i)).isoformat()
            bars.append([day, 100, 101, 99, 100, 10000])
        with gzip.open(self.path, "wt", encoding="utf-8") as stream:
            stream.write(json.dumps({"symbol": "EXAMPLE", "bars": bars}) + "\n")

    def test_existing_pilot_format_reaches_holdout(self):
        self.write_fixture()
        report = evaluate_pilot_artifact(
            self.path, cutoff=date(2025, 4, 1),
            holding_sessions=10, entry_stride=20)
        self.assertEqual(report["unique_symbols"], 1)
        self.assertGreater(report["candidate_count"], 0)
        self.assertGreater(report["result"]["training"]["trade_candidates"], 0)
        self.assertGreater(report["result"]["holdout"]["trade_candidates"], 0)
        self.assertFalse(report["historical_edge_proven"])

    def test_rejects_invalid_hold(self):
        self.write_fixture()
        with self.assertRaisesRegex(ValueError, "invalid_holding_sessions"):
            evaluate_pilot_artifact(
                self.path, cutoff=date(2025, 4, 1),
                holding_sessions=20)

    def test_rejects_overlapping_stride(self):
        self.write_fixture()
        with self.assertRaisesRegex(ValueError, "invalid_entry_stride"):
            evaluate_pilot_artifact(
                self.path, cutoff=date(2025, 4, 1),
                holding_sessions=10, entry_stride=5)


if __name__ == "__main__":
    unittest.main()
