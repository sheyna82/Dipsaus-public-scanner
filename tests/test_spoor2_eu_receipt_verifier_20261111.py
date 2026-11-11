import unittest
from datetime import datetime, timezone
from research.spoor2_eu_evidence_receipt_20261111 import build_eu_evidence_receipt
from research.spoor2_eu_receipt_verifier_20261111 import verify_eu_evidence_receipt

NOW=datetime(2026,11,11,10,tzinfo=timezone.utc)
def fixture():
    return {r+"_evidence":{"source_record_id":"fixture-"+r}
            for r in ("ask","target_bid","invalidation","fx","fees")}
def receipt(payload):
    return build_eu_evidence_receipt(payload,captured_utc=NOW)

class EuReceiptVerifierTests(unittest.TestCase):
    def test_independent_recomputation_matches(self):
        p=fixture()
        v=verify_eu_evidence_receipt(p,receipt(p))
        self.assertTrue(v["receipt_verified"])
        self.assertFalse(v["trade_ready"])
        self.assertIn("EXTERNAL_SOURCE_ATTESTATION_NOT_CONNECTED",v["blocks"])
    def test_modified_payload_fails(self):
        p=fixture()
        r=receipt(p)
        p["ask_evidence"]["source_record_id"]="modified"
        self.assertIn("RECEIPT_SHA256_MISMATCH",verify_eu_evidence_receipt(p,r)["blocks"])
    def test_modified_digest_fails(self):
        p=fixture()
        r=receipt(p)
        r["payload_sha256"]="0"*64
        self.assertIn("RECEIPT_SHA256_MISMATCH",verify_eu_evidence_receipt(p,r)["blocks"])
    def test_byte_count_mismatch_fails(self):
        p=fixture()
        r=receipt(p)
        r["payload_bytes"]+=1
        self.assertIn("RECEIPT_BYTE_LENGTH_MISMATCH",verify_eu_evidence_receipt(p,r)["blocks"])
    def test_schema_mismatch_fails(self):
        p=fixture()
        r=receipt(p)
        r["schema"]="unknown"
        self.assertIn("RECEIPT_SCHEMA_MISMATCH",verify_eu_evidence_receipt(p,r)["blocks"])
    def test_roles_mismatch_fails(self):
        p=fixture()
        r=receipt(p)
        r["record_roles"]=[]
        self.assertIn("RECEIPT_ROLES_MISMATCH",verify_eu_evidence_receipt(p,r)["blocks"])
    def test_timestamp_missing_fails(self):
        p=fixture()
        r=receipt(p)
        r.pop("captured_utc")
        self.assertIn("RECEIPT_TIMESTAMP_INVALID",verify_eu_evidence_receipt(p,r)["blocks"])
    def test_float_fails(self):
        p=fixture()
        r=receipt(p)
        p["ask_evidence"]["value"]=1.5
        self.assertIn("NONCANONICAL_EVIDENCE",verify_eu_evidence_receipt(p,r)["blocks"])
    def test_invalid_input_fails(self):
        self.assertIn("INVALID_VERIFICATION_INPUT",verify_eu_evidence_receipt(None,{})["blocks"])

if __name__=="__main__":
    unittest.main()
