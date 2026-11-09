import unittest
import hashlib,base64
from research_europe_benchmark_identity_receipt import validate_receipt
def fixture():
    return {"symbol":"SYNTHETIC.EU","provider_symbol":"^TEST",
            "official_index_name":"Synthetic Index","official_publisher":"Synthetic",
            "official_source_url":"https://example.org/synthetic",
            "official_document_sha256":hashlib.sha256(b"synthetic official document").hexdigest(),
            "official_document_base64":base64.b64encode(b"synthetic official document").decode(),
            "retrieval_method":"direct_https_no_redirect","retrieved_utc":"2026-11-09T12:00:00+00:00","reviewer":"synthetic-test",
            "review_day":"2026-11-09","methodology":"synthetic fixture only",
            "identity_match":True,"currency_match":True,
            "price_vs_total_return_match":True,"value_discrepancy_resolved":True}
class Tests(unittest.TestCase):
    def test_receipt_deterministic(self):
        a=validate_receipt(fixture());b=validate_receipt(fixture())
        self.assertEqual(a,b)
        self.assertFalse(a["trade_ready"])
        self.assertFalse(a["independently_audited"])
    def test_unverified_retrieval_method_blocks(self):
        r=fixture();r["retrieval_method"]="copied_from_webpage"
        with self.assertRaisesRegex(ValueError,"UNVERIFIED_RETRIEVAL_METHOD"):validate_receipt(r)
    def test_naive_retrieval_timestamp_blocks(self):
        r=fixture();r["retrieved_utc"]="2026-11-09T12:00:00"
        with self.assertRaisesRegex(ValueError,"INVALID_RETRIEVAL_TIMESTAMP"):validate_receipt(r)
    def test_nasdaq_publisher_requires_official_host(self):
        r=fixture();r["official_publisher"]="Nasdaq"
        r["official_source_url"]="https://example.org/synthetic"
        with self.assertRaisesRegex(ValueError,"OFFICIAL_PUBLISHER_HOST_MISMATCH"):validate_receipt(r)
    def test_nasdaq_official_host_allowed_but_not_independently_approved(self):
        r=fixture();r["official_publisher"]="Nasdaq"
        r["official_source_url"]="https://indexes.nasdaqomx.com/docs/Index_Versions_OMXH25.pdf"
        result=validate_receipt(r)
        self.assertFalse(result["independently_audited"])
        self.assertFalse(result["trade_ready"])
    def test_deceptive_url_username_blocks(self):
        r=fixture();r["official_publisher"]="Nasdaq"
        r["official_source_url"]="https://indexes.nasdaqomx.com@evil.example/forged"
        with self.assertRaisesRegex(ValueError,"INVALID_OFFICIAL_SOURCE"):validate_receipt(r)
    def test_modified_document_bytes_block(self):
        r=fixture();r["official_document_base64"]=base64.b64encode(b"altered").decode()
        with self.assertRaisesRegex(ValueError,"OFFICIAL_DOCUMENT_HASH_MISMATCH"):validate_receipt(r)
    def test_missing_document_bytes_block(self):
        r=fixture();del r["official_document_base64"]
        with self.assertRaisesRegex(ValueError,"MISSING_EVIDENCE"):validate_receipt(r)
    def test_missing_evidence(self):
        r=fixture();del r["official_publisher"]
        with self.assertRaisesRegex(ValueError,"MISSING_EVIDENCE"):validate_receipt(r)
    def test_discrepancy_blocks(self):
        r=fixture();r["value_discrepancy_resolved"]=False
        with self.assertRaisesRegex(ValueError,"UNRESOLVED_BENCHMARK_EVIDENCE"):
            validate_receipt(r)
    def test_unverified_price_return_blocks(self):
        r=fixture();r["price_vs_total_return_match"]=False
        with self.assertRaisesRegex(ValueError,"UNRESOLVED_BENCHMARK_EVIDENCE"):
            validate_receipt(r)
    def test_missing_document_hash(self):
        r=fixture();r["official_document_sha256"]="unknown"
        with self.assertRaisesRegex(ValueError,"INVALID_EVIDENCE_HASH"):validate_receipt(r)
if __name__=="__main__":unittest.main()
