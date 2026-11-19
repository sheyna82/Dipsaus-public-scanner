import hashlib
import unittest
from io import BytesIO
from research_capture_official_index_document import capture_official_document
from research_europe_benchmark_identity_receipt import validate_receipt

URL="https://indexes.nasdaqomx.com/docs/Index_Versions_OMXH25.pdf"

class FakeResponse:
    def __init__(self,body=b"%PDF-synthetic",url=URL,code=200):
        self.body=BytesIO(body);self.url=url;self.code=code
    def __enter__(self):return self
    def __exit__(self,*args):pass
    def geturl(self):return self.url
    def getcode(self):return self.code
    def read(self,n):return self.body.read(n)

class FakeOpener:
    def __init__(self,response):self.response=response
    def open(self,request,timeout):return self.response

class Tests(unittest.TestCase):
    def test_reproducible_source_receipt_remains_unapproved(self):
        r=capture_official_document(URL,opener=FakeOpener(FakeResponse()))
        self.assertEqual(r["official_document_sha256"],hashlib.sha256(b"%PDF-synthetic").hexdigest())
        self.assertFalse(r["independently_audited"])
        self.assertFalse(r["trade_ready"])
    def test_spoofed_host_blocked_before_network(self):
        with self.assertRaisesRegex(ValueError,"OFFICIAL_SOURCE_URL_BLOCKED"):
            capture_official_document("https://indexes.nasdaqomx.com@evil.example/file.pdf")
    def test_changed_response_url_blocked(self):
        with self.assertRaisesRegex(ValueError,"OFFICIAL_SOURCE_RESPONSE_BLOCKED"):
            capture_official_document(URL,opener=FakeOpener(FakeResponse(url="https://evil.example")))
    def test_capture_integrates_with_official_receipt_contract(self):
        captured=capture_official_document(URL,opener=FakeOpener(FakeResponse()))
        receipt={**captured,"symbol":"SYNTHETIC.EU","provider_symbol":"^TEST",
                 "official_index_name":"Synthetic Index","official_publisher":"Nasdaq",
                 "reviewer":"synthetic-test","review_day":"2026-11-09",
                 "methodology":"synthetic fixture", "identity_match":True,
                 "currency_match":True,"price_vs_total_return_match":True,
                 "value_discrepancy_resolved":True}
        validated=validate_receipt(receipt)
        self.assertFalse(validated["independently_audited"])
        self.assertFalse(validated["trade_ready"])
    def test_html_disguised_as_pdf_blocks(self):
        with self.assertRaisesRegex(ValueError,"OFFICIAL_SOURCE_NOT_PDF"):
            capture_official_document(URL,opener=FakeOpener(FakeResponse(body=b"<html>blocked</html>")))
    def test_oversized_document_blocked(self):
        with self.assertRaisesRegex(ValueError,"OFFICIAL_SOURCE_SIZE_BLOCKED"):
            capture_official_document(URL,opener=FakeOpener(FakeResponse(body=b"x"*2000001)))
if __name__=="__main__":unittest.main()
