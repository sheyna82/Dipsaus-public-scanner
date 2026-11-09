"""Offline issuer raw capture tests; no network and no authenticity claims."""
import base64
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from research_capture_omxh25_issuer_raw import capture

class Response:
    status = 200
    headers = {"Content-Type": "application/json"}
    def __init__(self, url):
        self.url = url
    def __enter__(self):
        return self
    def __exit__(self, *args):
        return False
    def geturl(self):
        return self.url
    def read(self, n):
        return b'{"illustrative":true}'

class RawCaptureTests(unittest.TestCase):
    def test_raw_bytes_preserved_without_approval(self):
        url = "https://indexes.nasdaqomx.com/index/history/omxh25"
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "receipt.json"
            result = capture(url, output, fetch=lambda request, timeout: Response(request.full_url))
            receipt = json.loads(output.read_text())
            self.assertEqual(result["status"], "raw_issuer_candidate_captured_unverified")
            self.assertEqual(base64.b64decode(receipt["source_raw_base64"]), b'{"illustrative":true}')
            self.assertEqual(receipt["source_sha256"], hashlib.sha256(b'{"illustrative":true}').hexdigest())
            self.assertFalse(receipt["benchmark_identity_verified"])
            self.assertFalse(receipt["trade_ready"])
            with self.assertRaises(FileExistsError):
                capture(url, output, fetch=lambda request, timeout: Response(request.full_url))

    def test_reject_untrusted_host(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError, "SOURCE_URL_NOT_ALLOWED"):
                capture("https://indexes.nasdaqomx.com.evil.test/eod",
                        Path(directory) / "receipt.json", fetch=lambda request, timeout: Response(request.full_url))

    def test_reject_redirected_final_url(self):
        class Redirected(Response):
            def geturl(self):
                return "https://evil.test/other"
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError, "SOURCE_URL_CHANGED"):
                capture("https://indexes.nasdaqomx.com/index/history/omxh25",
                        Path(directory) / "receipt.json",
                        fetch=lambda request, timeout: Redirected(request.full_url))

if __name__ == "__main__":
    unittest.main()
