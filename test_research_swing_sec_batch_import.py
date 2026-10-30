import json
import tempfile
import unittest
from pathlib import Path
from research_swing_sec_batch_import import import_sec_json_files

def payload(cik=320193, accession="0000320193-26-000001"):
    return {"cik": cik, "filings": {"recent": {
        "accessionNumber": [accession], "form": ["8-K"],
        "filingDate": ["2026-10-26"],
        "acceptanceDateTime": ["2026-10-26T17:03:00-04:00"],
        "primaryDocument": ["report.htm"]}}}

class SECBatchImportTests(unittest.TestCase):
    def test_import_actual_json_structure_and_provenance(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "filings.json"
            path.write_text(json.dumps(payload()), encoding="utf-8")
            result = import_sec_json_files([path])
            self.assertEqual(result["candidate_count"], 1)
            self.assertEqual(len(result["sources"][0]["sha256"]), 64)
            self.assertFalse(result["historical_release_times_verified"])
            self.assertFalse(result["candidates"][0]["trade_ready"])
    def test_reject_duplicate_across_files(self):
        with tempfile.TemporaryDirectory() as folder:
            paths = [Path(folder) / name for name in ("a.json", "b.json")]
            for path in paths:
                path.write_text(json.dumps(payload()), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "duplicate_filing_across_files"):
                import_sec_json_files(paths)
    def test_reject_empty_batch(self):
        with self.assertRaisesRegex(ValueError, "no_input_files"):
            import_sec_json_files([])
    def test_multiple_companies(self):
        with tempfile.TemporaryDirectory() as folder:
            a, b = Path(folder) / "a.json", Path(folder) / "b.json"
            a.write_text(json.dumps(payload()), encoding="utf-8")
            b.write_text(json.dumps(payload(1000045, "0001000045-26-000001")), encoding="utf-8")
            self.assertEqual(import_sec_json_files([a, b])["candidate_count"], 2)

if __name__ == "__main__":
    unittest.main()
