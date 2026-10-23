"""Synthetic local CLI smoke and guard tests."""
import contextlib
import io
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path
from research_chronological_atr_cli import main


def data(n=110):
    lines = ["date,open,high,low,close,volume"]
    for i in range(n):
        close = 100 + i * .1
        lines.append(f"{date(2025,1,1)+timedelta(days=i)},{close},{close+1},{close-1},{close},100")
    return ("\n".join(lines) + "\n").encode()


class CliTests(unittest.TestCase):
    def test_local_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            stock = Path(tmp) / "stock.csv"
            market = Path(tmp) / "benchmark.csv"
            stock.write_bytes(data())
            market.write_bytes(data())
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                result = main(["--stock-csv", str(stock), "--benchmark-csv", str(market),
                               "--split-date", "2025-03-27", "--horizon", "3"])
            self.assertFalse(result["trade_ready"])
            self.assertIn("atr_minus_baseline_brier", out.getvalue())

    def test_rejects_same_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            file = Path(tmp) / "stock.csv"
            file.write_bytes(data())
            with contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit):
                    main(["--stock-csv", str(file), "--benchmark-csv", str(file),
                          "--split-date", "2025-03-27"])


if __name__ == "__main__":
    unittest.main()
