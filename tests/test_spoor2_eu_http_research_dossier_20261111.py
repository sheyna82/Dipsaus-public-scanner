import hashlib
import unittest
from datetime import datetime,timezone
from research.spoor2_eu_http_research_dossier_20261111 import evaluate_eu_http_research_dossier
from tests.test_spoor2_eu_research_chain_20261111 import sample
NOW=datetime(2026,11,11,10,tzinfo=timezone.utc)
RAW=b'{"ask":"125.5","unit":"GBp"}'
def envelope():
    url="https://example.org/quotes"
    return dict(provider_id="exchange",source_record_id="offline-fixture",
        source_url=url,final_url=url,captured_utc=NOW.isoformat(),
        content_sha256=hashlib.sha256(RAW).hexdigest(),content_bytes=len(RAW),
        http_status=200,request_method="GET",redirect_count=0,
        transport="https",response_headers={"content-type":"application/json"})
class EuHttpDossierTests(unittest.TestCase):
    def test_complete_dossier_is_only_research(self):
        r=evaluate_eu_http_research_dossier(sample(),http_record=envelope(),raw_bytes=RAW,now_utc=NOW)
        self.assertEqual(r["status"],"RESEARCH_ONLY")
        self.assertFalse(r["external_source_attested"])
        self.assertFalse(r["trade_ready"])
        self.assertIn("TRUSTED_HTTP_FETCHER_NOT_CONNECTED",r["blocks"])
        self.assertIn("EXTERNAL_SOURCE_ATTESTATION_NOT_CONNECTED",r["blocks"])
    def test_tampered_body_blocks_before_chain(self):
        r=evaluate_eu_http_research_dossier(sample(),http_record=envelope(),raw_bytes=RAW+b"!",now_utc=NOW)
        self.assertEqual(r["status"],"BLOCKED")
        self.assertEqual(r["notification_channel"],"NONE")
        self.assertNotIn("research_chain",r)
    def test_non_get_blocks(self):
        e=envelope();e["request_method"]="POST"
        r=evaluate_eu_http_research_dossier(sample(),http_record=e,raw_bytes=RAW,now_utc=NOW)
        self.assertIn("HTTP_METHOD_NOT_READ_ONLY_GET",r["blocks"])
    def test_missing_candidate_blocks(self):
        r=evaluate_eu_http_research_dossier(None,http_record=envelope(),raw_bytes=RAW,now_utc=NOW)
        self.assertEqual(r["status"],"BLOCKED")
        self.assertFalse(r["trade_ready"])
    def test_source_separation_still_blocks(self):
        d=sample();d["target_bid_evidence"]["provider_id"]=d["ask_evidence"]["provider_id"]
        r=evaluate_eu_http_research_dossier(d,http_record=envelope(),raw_bytes=RAW,now_utc=NOW)
        self.assertEqual(r["status"],"BLOCKED")
        self.assertIn("BROKER_TECHNICAL_SOURCE_NOT_SEPARATED",r["blocks"])
if __name__=="__main__":
    unittest.main()
