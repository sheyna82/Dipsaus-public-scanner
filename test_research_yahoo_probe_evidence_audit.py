import hashlib
import json
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
from research_yahoo_probe_evidence_audit import audit_yahoo_probe


class ProbeEvidenceTests(unittest.TestCase):
    def fixture(self, root):
        stamps = [int(datetime.fromisoformat(x).replace(tzinfo=ZoneInfo("America/New_York")).timestamp())
                  for x in ("2026-11-02T12:00:00", "2026-11-03T12:00:00")]
        payload = {"chart": {"error": None, "result": [{"meta": {"symbol": "AMD"},
            "timestamp": stamps, "indicators": {"quote": [{"close": [100, 101]}]}}]}}
        raw = json.dumps(payload).encode()
        (root / "yahoo-AMD-raw.json").write_bytes(raw)
        (root / "yahoo-AMD-normalized.json").write_text(json.dumps([
            {"date": "2026-11-02", "close": "100"},
            {"date": "2026-11-03", "close": "101"}]))
        (root / "yahoo-AMD-validation.json").write_text(json.dumps({
            "provider": "yahoo_chart", "symbol": "AMD", "status": "normalized_unverified",
            "raw_sha256": hashlib.sha256(raw).hexdigest(),
            "retrieved_at_utc": "2026-11-03T14:57:22+00:00"}))

    def test_hash_and_same_day_exclusion(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.fixture(root)
            result = audit_yahoo_probe(root, "AMD")
            self.assertEqual(result["last_conservatively_eligible_session"], "2026-11-02")
            self.assertEqual(result["same_day_rows_excluded"], 1)
            self.assertFalse(result["prospective_candidate_registered"])

    def test_tampered_raw_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.fixture(root)
            (root / "yahoo-AMD-raw.json").write_bytes(b"{}")
            with self.assertRaisesRegex(ValueError, "raw_payload_hash_mismatch"):
                audit_yahoo_probe(root, "AMD")

    def test_tampered_normalization_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.fixture(root)
            (root / "yahoo-AMD-normalized.json").write_text("[]")
            with self.assertRaisesRegex(ValueError, "normalized_price_mismatch"):
                audit_yahoo_probe(root, "AMD")


if __name__ == "__main__":
    unittest.main()
