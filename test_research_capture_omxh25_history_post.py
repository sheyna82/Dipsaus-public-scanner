import base64
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from research_capture_omxh25_history_post import capture_history_post, ENDPOINT

class FakeResponse:
    status = 200
    headers = {"Content-Type": "application/json; charset=utf-8"}
    def __enter__(self):
        return self
    def __exit__(self, *args):
        return False
    def geturl(self):
        return ENDPOINT
    def read(self, count):
        return b'{"illustrative":true}'

class HistoryPostTests(unittest.TestCase):
    def test_preserves_request_and_raw_response_without_promotion(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "receipt.json"
            def fetch(request, timeout):
                self.assertEqual(request.get_method(), "POST")
                self.assertIn(b"id=OMXH25", request.data)
                return FakeResponse()
            result = capture_history_post(path, "2026-11-05T00:00:00",
                                          "2026-11-09T00:00:00", "0", fetch=fetch)
            receipt = json.loads(path.read_text())
            self.assertEqual(base64.b64decode(receipt["source_raw_base64"]), b'{"illustrative":true}')
            self.assertEqual(receipt["source_sha256"], hashlib.sha256(b'{"illustrative":true}').hexdigest())
            self.assertFalse(receipt["official_eod_raw_bytes_verified"])
            self.assertFalse(receipt["trade_ready"])
            self.assertEqual(result["status"], "history_post_raw_captured_unverified")
            with self.assertRaises(FileExistsError):
                capture_history_post(path, "2026-11-05T00:00:00",
                                     "2026-11-09T00:00:00", "0", fetch=fetch)

    def test_reject_invalid_date(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError, "UNREVIEWED_DATE_FORMAT"):
                capture_history_post(Path(directory)/"x.json", "yesterday", "tomorrow", "0")

    def test_reject_invalid_time_of_day(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError, "UNREVIEWED_TIME_OF_DAY"):
                capture_history_post(Path(directory)/"x.json", "2026-11-05T00:00:00",
                                     "2026-11-09T00:00:00", "a&b")

if __name__ == "__main__":
    unittest.main()
