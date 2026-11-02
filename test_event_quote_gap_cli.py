"""Offline CLI regression tests: no raw prices, symbols, or exception paths."""
import contextlib
from io import StringIO
import json
import tempfile
from pathlib import Path
import unittest
from event_quote_gap_cli import main

class EventQuoteGapCliTests(unittest.TestCase):
    def run_cli(self, path):
        output = StringIO()
        with contextlib.redirect_stdout(output):
            code = main([str(path), "--now", "2026-11-02T15:00:00+00:00"])
        return code, json.loads(output.getvalue())

    def test_local_watch_report_redacts_values(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "private-watch.json"
            path.write_text(json.dumps({"rows": [{"symbol": "PLTR",
                "provider_quote": 123.45,
                "provider_quote_utc": "2026-11-02T14:59:00+00:00",
                "provider_freshness_pass": True}]}), encoding="utf-8")
            code, result = self.run_cli(path)
            self.assertEqual(code, 0)
            self.assertEqual(result["blocked"], 1)
            self.assertNotIn("PLTR", str(result))
            self.assertNotIn("123.45", str(result))
            self.assertFalse(result["execution_ready"])

    def test_invalid_json_never_exposes_path(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "sensitive-name.json"
            path.write_text("{broken", encoding="utf-8")
            code, result = self.run_cli(path)
            self.assertEqual(code, 2)
            self.assertEqual(result["status"], "INPUT_ERROR")
            self.assertNotIn("sensitive-name", str(result))

    def test_invalid_input_shape_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "rows.json"
            path.write_text('{"rows": {"symbol": "PLTR"}}', encoding="utf-8")
            code, result = self.run_cli(path)
            self.assertEqual(code, 2)
            self.assertEqual(result["status"], "INVALID_INPUT")

if __name__ == "__main__":
    unittest.main()
