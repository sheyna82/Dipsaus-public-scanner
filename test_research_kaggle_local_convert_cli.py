"""Synthetic tests for local Kaggle conversion command."""
import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from research_kaggle_local_convert_cli import main

SAMPLE = b"Date,Open,High,Low,Close,Volume,OpenInt\n2017-01-03,10,12,9,11,1000,0\n"


class LocalConversionTests(unittest.TestCase):
    def test_private_output(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "input.csv").write_bytes(SAMPLE)
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                code = main(["--source", str(root / "input.csv"),
                             "--output", str(root / "converted.csv")])
            self.assertEqual(code, 0)
            self.assertEqual((root / "converted.csv").read_bytes(),
                             b"date,open,high,low,close,volume\n2017-01-03,10,12,9,11,1000\n")
            self.assertEqual((root / "converted.csv").stat().st_mode & 0o777, 0o600)
            self.assertNotIn("2017-01-03", output.getvalue())
            self.assertFalse(json.loads(output.getvalue())["trade_ready"])

    def test_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "input.csv").write_bytes(SAMPLE)
            (root / "converted.csv").write_text("preserve me")
            with contextlib.redirect_stdout(io.StringIO()):
                code = main(["--source", str(root / "input.csv"),
                             "--output", str(root / "converted.csv")])
            self.assertEqual(code, 1)
            self.assertEqual((root / "converted.csv").read_text(), "preserve me")


if __name__ == "__main__":
    unittest.main()
