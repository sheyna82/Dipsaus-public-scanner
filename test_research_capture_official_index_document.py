import hashlib
import unittest
from io import BytesIO
from research_capture_official_index_document import capture_official_document

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
    def test_oversized_document_blocked(self):
        with self.assertRaisesRegex(ValueError,"OFFICIAL_SOURCE_SIZE_BLOCKED"):
            capture_official_document(URL,opener=FakeOpener(FakeResponse(body=b"x"*2000001)))
if __name__=="__main__":unittest.main()
