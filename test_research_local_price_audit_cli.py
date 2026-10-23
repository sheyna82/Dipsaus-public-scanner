"""No-network CLI tests with synthetic local fixtures."""
import contextlib
import hashlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from research_local_price_audit_cli import main

DATA = b"date,open,high,low,close,volume\n2026-01-02,10,12,9,11,100\n"


def metadata():
    return {
        "provider": "synthetic fixture",
        "dataset": "synthetic",
        "source_url": "https://example.org/synthetic",
        "license_reference": "synthetic fixture only",
        "retrieved_at": "2026-10-23T10:00:00+00:00",
        "sha256": hashlib.sha256(DATA).hexdigest(),
        "adjustment_policy": "unadjusted",
        "universe_policy": "single synthetic instrument",
    }


class LocalAuditCliTests(unittest.TestCase):
    def test_local_success_only_emits_summary(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "bars.csv").write_bytes(DATA)
            (root / "manifest.json").write_text(json.dumps(metadata()), encoding="utf-8")
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                code = main(["--manifest", str(root / "manifest.json"),
                             "--csv", str(root / "bars.csv")])
            self.assertEqual(code, 0)
            result = json.loads(output.getvalue())
            self.assertEqual(result["rows"], 1)
            self.assertFalse(result["research_data_ready"])
            self.assertNotIn("2026-01-02", output.getvalue())
            self.assertNotIn("10,12,9,11", output.getvalue())
            self.assertNotIn(str(root), output.getvalue())
            self.assertNotIn("example.org", output.getvalue())
            self.assertNotIn("synthetic fixture only", output.getvalue())

    def test_oversized_csv_rejected_before_read(self):
        from research_local_price_audit_cli import MAX_CSV_BYTES
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with (root / "bars.csv").open("wb") as handle:
                handle.truncate(MAX_CSV_BYTES + 1)
            (root / "manifest.json").write_text(json.dumps(metadata()), encoding="utf-8")
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                code = main(["--manifest", str(root / "manifest.json"),
                             "--csv", str(root / "bars.csv")])
            self.assertEqual(code, 1)
            self.assertEqual(json.loads(output.getvalue())["error_type"], "ValueError")

    def test_symlink_input_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "bars.csv").write_bytes(DATA)
            (root / "alias.csv").symlink_to(root / "bars.csv")
            (root / "manifest.json").write_text(json.dumps(metadata()), encoding="utf-8")
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                code = main(["--manifest", str(root / "manifest.json"),
                             "--csv", str(root / "alias.csv")])
            self.assertEqual(code, 1)
            self.assertEqual(json.loads(output.getvalue())["error_type"], "ValueError")

    def test_local_failure_does_not_expose_prices(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "bars.csv").write_bytes(DATA + b"tampered")
            (root / "manifest.json").write_text(json.dumps(metadata()), encoding="utf-8")
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                code = main(["--manifest", str(root / "manifest.json"),
                             "--csv", str(root / "bars.csv")])
            self.assertEqual(code, 1)
            self.assertFalse(json.loads(output.getvalue())["accepted"])
            self.assertNotIn("tampered", output.getvalue())


if __name__ == "__main__":
    unittest.main()
