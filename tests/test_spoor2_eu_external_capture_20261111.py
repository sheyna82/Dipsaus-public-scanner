import hashlib
import unittest
from datetime import datetime,timezone
from research.spoor2_eu_external_capture_20261111 import audit_external_capture
NOW=datetime(2026,11,11,10,tzinfo=timezone.utc)
RAW=b'{"ask":"125.50","unit":"GBp"}'
def fixture():
    return dict(provider_id="exchange",source_record_id="sample-1",
        source_url="https://example.org/quotes",captured_utc=NOW.isoformat(),
        content_sha256=hashlib.sha256(RAW).hexdigest(),content_bytes=len(RAW))
class ExternalCaptureTests(unittest.TestCase):
    def test_matching_bytes_never_attested(self):
        r=audit_external_capture(fixture(),RAW,now_utc=NOW)
        self.assertEqual(r["status"],"CAPTURE_BYTES_MATCH_UNATTESTED")
        self.assertFalse(r["source_attested"])
        self.assertFalse(r["trade_ready"])
    def test_invalid_age_budgets_fail_closed(self):
        for budget in (True, -1, 86401, 1.5, "900", None):
            with self.subTest(budget=budget):
                result=audit_external_capture(fixture(),RAW,now_utc=NOW,max_age_seconds=budget)
                self.assertEqual(result["status"],"BLOCKED")
                self.assertEqual(result["blocks"],["INVALID_MAX_AGE"])
                self.assertFalse(result["source_attested"])
    def test_exact_zero_age_budget_is_valid_but_unattested(self):
        result=audit_external_capture(fixture(),RAW,now_utc=NOW,max_age_seconds=0)
        self.assertEqual(result["status"],"CAPTURE_BYTES_MATCH_UNATTESTED")
        self.assertFalse(result["source_attested"])
    def test_changed_bytes_blocked(self):
        self.assertIn("CAPTURE_CONTENT_HASH_MISMATCH",audit_external_capture(fixture(),RAW+b"!",now_utc=NOW)["blocks"])
    def test_wrong_length_blocked(self):
        d=fixture();d["content_bytes"]+=1
        self.assertIn("CAPTURE_CONTENT_LENGTH_MISMATCH",audit_external_capture(d,RAW,now_utc=NOW)["blocks"])
    def test_missing_metadata_blocked(self):
        d=fixture();d.pop("provider_id")
        self.assertIn("CAPTURE_METADATA_INCOMPLETE",audit_external_capture(d,RAW,now_utc=NOW)["blocks"])
    def test_future_capture_blocked(self):
        d=fixture();d["captured_utc"]="2026-11-12T10:00:00+00:00"
        self.assertIn("CAPTURE_STALE_OR_FUTURE",audit_external_capture(d,RAW,now_utc=NOW)["blocks"])
    def test_credentials_url_blocked(self):
        d=fixture();d["source_url"]="https://user:pass@example.org/quotes"
        self.assertIn("CAPTURE_URL_OR_TIME_INVALID",audit_external_capture(d,RAW,now_utc=NOW)["blocks"])
    def test_empty_bytes_blocked(self):
        self.assertIn("CAPTURE_EMPTY",audit_external_capture(fixture(),b"",now_utc=NOW)["blocks"])
    def test_nonbytes_blocked(self):
        self.assertIn("INVALID_CAPTURE_INPUT",audit_external_capture(fixture(),"raw",now_utc=NOW)["blocks"])
if __name__=="__main__":
    unittest.main()
