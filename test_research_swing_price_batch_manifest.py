"""Offline tests for deterministic historical price batch manifests."""
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path
from research_swing_price_batch_manifest import create_price_batch_manifest


def make_csv(path):
    rows = ["session_date,open,high,low,close,volume"]
    for i in range(15):
        rows.append(f"{(date(2026,9,1)+timedelta(days=i)).isoformat()},100,105,95,101,10000")
    path.write_text("\n".join(rows) + "\n", encoding="utf-8")


class ManifestTests(unittest.TestCase):
    def test_deterministic_and_unverified(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "a.csv"
            make_csv(path)
            options = {"provider_name": "experimental", "retrieved_at": "2026-10-26T12:00:00+00:00"}
            first = create_price_batch_manifest({"AAPL": path}, **options)
            second = create_price_batch_manifest({"AAPL": path}, **options)
            self.assertEqual(first["manifest_sha256"], second["manifest_sha256"])
            self.assertEqual(first["files"][0]["sessions"], 15)
            self.assertFalse(first["provider_authenticated"])

    def test_timezone_required(self):
        with self.assertRaisesRegex(ValueError, "timezone_required"):
            create_price_batch_manifest({"AAPL": "x.csv"},
                                        provider_name="test", retrieved_at="2026-10-26T12:00:00")

    def test_empty_batch_rejected(self):
        with self.assertRaisesRegex(ValueError, "empty_price_batch"):
            create_price_batch_manifest({}, provider_name="test",
                                        retrieved_at="2026-10-26T12:00:00+00:00")

    def test_invalid_csv_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad.csv"
            path.write_text("bad header\n")
            with self.assertRaisesRegex(ValueError, "unexpected_ohlcv_columns"):
                create_price_batch_manifest({"AAPL": path}, provider_name="test",
                                            retrieved_at="2026-10-26T12:00:00+00:00")


if __name__ == "__main__":
    unittest.main()
