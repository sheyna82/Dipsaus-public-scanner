"""Offline contract tests for isolated AMD historical capture; no network."""
import json
import tempfile
import unittest
from pathlib import Path
from research_capture_amd_history import collect

def fixture(symbol="AMD", count=110, bad=False):
    prices = [100.0] * count
    if bad:
        prices[0] = -1
    obj = {"chart": {"result": [{"meta": {"symbol": symbol},
        "timestamp": list(range(1700000000, 1700000000 + count * 60, 60)),
        "indicators": {"quote": [{"open": prices, "high": [102.0]*count,
        "low": [99.0]*count, "close": [101.0]*count,
        "volume": [1000]*count}]}}]}}
    return json.dumps(obj).encode()

class Response:
    status = 200
    def __init__(self, raw): self.raw = raw
    def __enter__(self): return self
    def __exit__(self, *args): return False
    def read(self, n): return self.raw[:n]

class CaptureTests(unittest.TestCase):
    def run_capture(self, data):
        with tempfile.TemporaryDirectory() as folder:
            dest = Path(folder) / "amd.json"
            result = collect(dest, fetch=lambda req, timeout: Response(data))
            return result, json.loads(dest.read_text())

    def test_valid_capture_is_research_only(self):
        result, output = self.run_capture(fixture())
        self.assertEqual(result["counts"], {"daily": 110, "intraday": 110})
        self.assertFalse(output["trade_ready"])
        self.assertTrue(output["research_only"])

    def test_wrong_symbol_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "symbol_mismatch"):
            self.run_capture(fixture(symbol="AAPL"))

    def test_insufficient_bars_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "insufficient"):
            self.run_capture(fixture(count=19))

    def test_invalid_bar_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "insufficient"):
            self.run_capture(fixture(count=20, bad=True))

    def test_capture_never_overwrites(self):
        with tempfile.TemporaryDirectory() as folder:
            dest = Path(folder) / "amd.json"
            dest.write_text("existing")
            with self.assertRaises(FileExistsError):
                collect(dest, fetch=lambda req, timeout: Response(fixture()))
            self.assertEqual(dest.read_text(), "existing")

if __name__ == "__main__":
    unittest.main()
