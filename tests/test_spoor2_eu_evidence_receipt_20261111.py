import unittest
from datetime import datetime, timezone
from research.spoor2_eu_evidence_receipt_20261111 import build_eu_evidence_receipt
NOW = datetime(2026, 11, 11, 10, tzinfo=timezone.utc)

def sample():
    return {role+"_evidence":{"source_record_id":"fixture-"+role}
            for role in ("ask","target_bid","invalidation","fx","fees")}

class EuropeanEvidenceReceiptTests(unittest.TestCase):
    def test_stable_across_key_order(self):
        a=sample()
        b=dict(reversed(list(a.items())))
        self.assertEqual(build_eu_evidence_receipt(a,captured_utc=NOW)["payload_sha256"],
                         build_eu_evidence_receipt(b,captured_utc=NOW)["payload_sha256"])
    def test_tampering_changes_hash(self):
        a=sample()
        b=sample()
        b["ask_evidence"]["source_record_id"]="changed"
        self.assertNotEqual(build_eu_evidence_receipt(a,captured_utc=NOW)["payload_sha256"],
                            build_eu_evidence_receipt(b,captured_utc=NOW)["payload_sha256"])
    def test_receipt_never_attests(self):
        r=build_eu_evidence_receipt(sample(),captured_utc=NOW)
        self.assertEqual(r["status"],"LOCAL_RECEIPT_ONLY")
        self.assertFalse(r["trade_ready"])
        self.assertIn("EXTERNAL_SOURCE_ATTESTATION_NOT_CONNECTED",r["blocks"])
    def test_missing_role_blocks(self):
        d=sample()
        d.pop("fx_evidence")
        self.assertIn("EVIDENCE_RECORD_MISSING",build_eu_evidence_receipt(d,captured_utc=NOW)["blocks"])
    def test_float_blocks(self):
        d=sample()
        d["ask_evidence"]["observed_price"]=1.25
        self.assertIn("NONCANONICAL_EVIDENCE",build_eu_evidence_receipt(d,captured_utc=NOW)["blocks"])
    def test_nonfinite_blocks(self):
        d=sample()
        d["ask_evidence"]["observed_price"]=float("nan")
        self.assertIn("NONCANONICAL_EVIDENCE",build_eu_evidence_receipt(d,captured_utc=NOW)["blocks"])
    def test_bad_input_blocks(self):
        self.assertIn("INVALID_RECEIPT_INPUT",build_eu_evidence_receipt(None,captured_utc=NOW)["blocks"])

if __name__=="__main__":
    unittest.main()
