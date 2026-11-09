"""Offline negative tests for OMXH25 primary issuer EOD provenance gate."""
import base64
import copy
import hashlib
import json
import unittest
from research_review_omxh25_official_eod import review_official_eod_evidence

def evidence():
    raw = json.dumps({'session': {'date': '2026-11-06', 'index': 'OMXH25', 'close': 6221.79}}).encode()
    return {"source_url": "https://indexes.nasdaqomx.com/index/history/omxh25",
            "retrieved_utc": "2026-11-09T15:00:00+00:00",
            "source_sha256": hashlib.sha256(raw).hexdigest(),
            "source_raw_base64": base64.b64encode(raw).decode(),
            "session_date": "2026-11-06", "official_index": "OMXH25",
            "currency": "EUR", "return_type": "PRICE_RETURN",
            "close_field": "/session/close", "close_value": 6221.79,
            "extraction_method": "reviewed_issuer_dated_eod_field"}

class ProvenanceGateTests(unittest.TestCase):
    def test_self_consistency_does_not_approve_authenticity(self):
        result = review_official_eod_evidence(evidence())
        self.assertFalse(result["source_authenticity_independently_verified"])
        self.assertFalse(result["benchmark_identity_verified"])
        self.assertFalse(result["trade_ready"])

    def test_reject_tampered_hash(self):
        doc = evidence()
        doc["source_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "HASH_MISMATCH"):
            review_official_eod_evidence(doc)

    def test_reject_untrusted_host(self):
        doc = evidence()
        doc["source_url"] = "https://nasdaq.com.evil.example/eod"
        with self.assertRaisesRegex(ValueError, "UNAPPROVED_SOURCE"):
            review_official_eod_evidence(doc)

    def test_reject_total_return_variant(self):
        doc = evidence()
        doc["return_type"] = "GROSS_TOTAL_RETURN"
        with self.assertRaisesRegex(ValueError, "INDEX_VARIANT"):
            review_official_eod_evidence(doc)

    def test_reject_undated_issuer_extraction(self):
        doc = evidence()
        doc["extraction_method"] = "guess"
        with self.assertRaisesRegex(ValueError, "UNREVIEWED_EXTRACTION"):
            review_official_eod_evidence(doc)

    def test_reject_claimed_close_not_in_raw_bytes(self):
        doc = evidence()
        doc["close_value"] = 6221.80
        with self.assertRaisesRegex(ValueError, "RAW_CLOSE_FIELD_MISMATCH"):
            review_official_eod_evidence(doc)

    def test_reject_unsupported_html_extraction(self):
        doc = evidence()
        doc["close_field"] = "html:span.close"
        with self.assertRaisesRegex(ValueError, "UNSUPPORTED_CLOSE_FIELD"):
            review_official_eod_evidence(doc)

    def test_reject_duplicate_close_keys(self):
        doc = evidence()
        raw = b'{"session":{"date":"2026-11-06","index":"OMXH25","close":1,"close":6221.79}}'
        doc["source_raw_base64"] = base64.b64encode(raw).decode()
        doc["source_sha256"] = hashlib.sha256(raw).hexdigest()
        with self.assertRaisesRegex(ValueError, "RAW_CLOSE_EXTRACTION_FAILED"):
            review_official_eod_evidence(doc)

    def test_reject_nonfinite_raw_json(self):
        doc = evidence()
        raw = b'{"session":{"date":"2026-11-06","index":"OMXH25","close":6221.79,"extra":NaN}}'
        doc["source_raw_base64"] = base64.b64encode(raw).decode()
        doc["source_sha256"] = hashlib.sha256(raw).hexdigest()
        with self.assertRaisesRegex(ValueError, "RAW_CLOSE_EXTRACTION_FAILED"):
            review_official_eod_evidence(doc)

    def test_reject_naive_retrieval_time(self):
        doc = evidence()
        doc["retrieved_utc"] = "2026-11-09T15:00:00"
        with self.assertRaisesRegex(ValueError, "RETRIEVAL_NOT_UTC"):
            review_official_eod_evidence(doc)

if __name__ == "__main__":
    unittest.main()
