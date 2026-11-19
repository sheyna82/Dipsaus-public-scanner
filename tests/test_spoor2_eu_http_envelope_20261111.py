import hashlib
import unittest
from datetime import datetime, timezone
from research.spoor2_eu_http_envelope_20261111 import review_http_capture_envelope
NOW=datetime(2026,11,11,10,tzinfo=timezone.utc)
RAW=b'{"ask":"125.50","unit":"GBp"}'
def fixture():
    url="https://example.org/quotes"
    return dict(provider_id="example",source_record_id="offline-1",
        source_url=url,final_url=url,captured_utc=NOW.isoformat(),
        content_sha256=hashlib.sha256(RAW).hexdigest(),content_bytes=len(RAW),
        http_status=200,request_method="GET",redirect_count=0,
        transport="https",response_headers={"content-type":"application/json"})
class HttpEnvelopeTests(unittest.TestCase):
    def test_valid_envelope_still_unattested(self):
        r=review_http_capture_envelope(fixture(),RAW,now_utc=NOW)
        self.assertEqual(r["status"],"HTTP_ENVELOPE_REVIEW_ONLY")
        self.assertFalse(r["http_origin_attested"])
        self.assertFalse(r["trade_ready"])
    def test_non_200_blocks(self):
        d=fixture();d["http_status"]=404
        self.assertIn("HTTP_STATUS_NOT_OK",review_http_capture_envelope(d,RAW,now_utc=NOW)["blocks"])
    def test_post_blocks(self):
        d=fixture();d["request_method"]="POST"
        self.assertIn("HTTP_METHOD_NOT_READ_ONLY_GET",review_http_capture_envelope(d,RAW,now_utc=NOW)["blocks"])
    def test_redirect_blocks(self):
        d=fixture();d["redirect_count"]=1
        self.assertIn("HTTP_REDIRECTS_NOT_ALLOWED",review_http_capture_envelope(d,RAW,now_utc=NOW)["blocks"])
    def test_final_url_mismatch_blocks(self):
        d=fixture();d["final_url"]="https://example.org/other"
        self.assertIn("HTTP_FINAL_URL_MISMATCH",review_http_capture_envelope(d,RAW,now_utc=NOW)["blocks"])
    def test_transport_mismatch_blocks(self):
        d=fixture();d["transport"]="http"
        self.assertIn("HTTP_TRANSPORT_UNATTESTED",review_http_capture_envelope(d,RAW,now_utc=NOW)["blocks"])
    def test_invalid_headers_block(self):
        d=fixture();d["response_headers"]={"x-test":"value\\r\\nheader"}
        self.assertEqual(review_http_capture_envelope(d,RAW,now_utc=NOW)["status"],"HTTP_ENVELOPE_REVIEW_ONLY")
        d["response_headers"]={"x-test":"value\r\nheader"}
        self.assertIn("HTTP_HEADERS_INVALID",review_http_capture_envelope(d,RAW,now_utc=NOW)["blocks"])
    def test_tampered_body_blocks(self):
        self.assertIn("CAPTURE_CONTENT_HASH_MISMATCH",
            review_http_capture_envelope(fixture(),RAW+b"!",now_utc=NOW)["blocks"])
if __name__=="__main__":
    unittest.main()
