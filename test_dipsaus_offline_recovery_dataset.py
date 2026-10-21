import json
import tempfile
import unittest
from pathlib import Path
from dipsaus_offline_recovery_dataset import load_recovery_jsonl, evaluate_recovery_jsonl


def observation():
    features = {"relative_strength_20d": 3, "return_5d": 2,
                "volume_ratio_20d": 1.5, "atr_pct": 3,
                "market_return_5d": 1, "days_to_earnings": 10}
    return {"id": "synthetic-1", "signal_time": "2026-10-01T16:00:00+00:00",
            "features": features,
            "provenance": {k: {"observed_at": "2026-09-30T16:00:00+00:00",
                               "published_at": "2026-09-30T16:05:00+00:00"}
                           for k in features},
            "bars": [{"date": "2026-10-01", "high": 101, "low": 99, "close": 100},
                     {"date": "2026-10-02", "high": 104, "low": 99, "close": 103}]}


class DatasetTests(unittest.TestCase):
    def test_local_dataset_runs_without_data_provider(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "observations.jsonl"
            path.write_text(json.dumps(observation()) + "\n", encoding="utf-8")
            r = evaluate_recovery_jsonl(path, minimum_resolved=1, horizon=1)
            self.assertEqual(r["included"], 1)
            self.assertFalse(r["source_verified"])
            self.assertFalse(r["historical_performance_validated"])
            self.assertFalse(r["trade_ready"])

    def test_rejects_malformed_json_and_non_object(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "invalid.jsonl"
            path.write_text("{bad", encoding="utf-8")
            self.assertIsNone(load_recovery_jsonl(path))
            path.write_text("[1,2,3]\n", encoding="utf-8")
            self.assertIsNone(load_recovery_jsonl(path))

    def test_rejects_record_limit_and_duplicate_ids(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "many.jsonl"
            path.write_text((json.dumps(observation()) + "\n") * 2, encoding="utf-8")
            self.assertIsNone(load_recovery_jsonl(path, max_records=1))
            self.assertIsNone(evaluate_recovery_jsonl(path, horizon=1))

    def test_rejects_nonfinite_json(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "nan.jsonl"
            path.write_text('{"id":NaN}', encoding="utf-8")
            self.assertIsNone(load_recovery_jsonl(path))


if __name__ == "__main__":
    unittest.main()
