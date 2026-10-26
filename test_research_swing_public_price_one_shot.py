"""No-network synthetic tests for one-shot public price acquisition."""
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path
from research_swing_public_price_one_shot import download_once


class Response:
    def __init__(self, data):
        self.data = data
    def __enter__(self):
        return self
    def __exit__(self, *args):
        return False
    def read(self, size):
        return self.data[:size]


def sample():
    lines = ["Date,Open,High,Low,Close,Volume"]
    for i in range(15):
        day = (date(2026, 9, 1) + timedelta(days=i)).isoformat()
        lines.append(f"{day},100,105,95,101,10000")
    return ("\n".join(lines) + "\n").encode()


class OneShotTests(unittest.TestCase):
    def test_network_off_by_default(self):
        with self.assertRaisesRegex(ValueError, "explicit_opt_in"):
            download_once("aapl.us", "unused.csv")

    def test_symbol_allowlist(self):
        with self.assertRaisesRegex(ValueError, "symbol_not_allowlisted"):
            download_once("unknown.us", "unused.csv", allow_network=True)

    def test_valid_mock_download(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "prices.csv"
            result = download_once("aapl.us", path, allow_network=True,
                                   opener=lambda req, timeout: Response(sample()))
            self.assertEqual(result["bars"], 15)
            self.assertFalse(result["license_verified"])
            self.assertEqual(path.read_bytes(), sample())

    def test_bad_provider_header(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "prices.csv"
            with self.assertRaisesRegex(ValueError, "unexpected_provider_header"):
                download_once("aapl.us", path, allow_network=True,
                              opener=lambda req, timeout: Response(b"wrong\n"))
            self.assertFalse(path.exists())

    def test_no_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "prices.csv"
            path.write_text("existing")
            with self.assertRaisesRegex(ValueError, "destination_already_exists"):
                download_once("aapl.us", path, allow_network=True)
            self.assertEqual(path.read_text(), "existing")


if __name__ == "__main__":
    unittest.main()
