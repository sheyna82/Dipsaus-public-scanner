"""Offline SEC candidate archive tamper tests."""
import hashlib
import json
import unittest
from datetime import datetime, timezone
from integrated_sec_candidate_archive import archive_sec_capture, verify_sec_archive

URL = ("https://www.sec.gov/Archives/edgar/data/123456/"
       "000012345626000001/0000123456-26-000001.txt")
RAW = (b"<SEC-HEADER>\n<ACCESSION-NUMBER>0000123456-26-000001\n"
       b"<ACCEPTANCE-DATETIME>20261105163000\n</SEC-HEADER>\n")


def fetch(url, agent):
    return RAW, {
        "schema": "sec_live_retrieval_receipt_v1",
        "source_url": url,
        "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
        "sha256": hashlib.sha256(RAW).hexdigest(),
        "byte_count": len(RAW),
        "historical_publication_independently_proven": False,
        "eligible_for_performance_claim": False,
        "trade_ready": False,
    }


class SecCandidateArchiveTests(unittest.TestCase):
    def test_original_bytes_and_dossier_verify(self):
        package = archive_sec_capture("c-001", URL, "2026-11-06T09:00:00-05:00",
                                      "research test", fetch)
        self.assertTrue(verify_sec_archive(package, RAW))
        self.assertFalse(package["manifest"]["historical_publication_independently_proven"])

    def test_changed_original_bytes_rejected(self):
        package = archive_sec_capture("c-001", URL, "2026-11-06T09:00:00-05:00",
                                      "research test", fetch)
        with self.assertRaisesRegex(ValueError, "SEC_ARCHIVE_BINDING_MISMATCH"):
            verify_sec_archive(package, RAW + b"x")

    def test_rehashed_dossier_with_forged_acceptance_rejected(self):
        package = archive_sec_capture("c-001", URL, "2026-11-06T09:00:00-05:00",
                                      "research test", fetch)
        dossier = package["capture"]["evidence_dossier"]
        dossier["dossier"]["sec_audit"]["acceptance_at_et"] = "2026-11-04T16:30:00-05:00"
        canonical = json.dumps(dossier["dossier"], sort_keys=True,
                               separators=(",", ":"), ensure_ascii=True)
        dossier["dossier_sha256"] = hashlib.sha256(canonical.encode("ascii")).hexdigest()
        package["manifest"]["dossier_sha256"] = dossier["dossier_sha256"]
        canonical_manifest = json.dumps(package["manifest"], sort_keys=True,
                                        separators=(",", ":"))
        package["manifest_sha256"] = hashlib.sha256(canonical_manifest.encode()).hexdigest()
        with self.assertRaisesRegex(ValueError, "SEC_ARCHIVE_RECOMPUTED_AUDIT_MISMATCH"):
            verify_sec_archive(package, RAW)

    def test_receipt_promotion_rejected(self):
        package = archive_sec_capture("c-001", URL, "2026-11-06T09:00:00-05:00",
                                      "research test", fetch)
        package["capture"]["retrieval_receipt"]["trade_ready"] = True
        with self.assertRaisesRegex(ValueError, "SEC_ARCHIVE_UNSUPPORTED_PROOF_PROMOTION"):
            verify_sec_archive(package, RAW)

    def test_modified_manifest_rejected(self):
        package = archive_sec_capture("c-001", URL, "2026-11-06T09:00:00-05:00",
                                      "research test", fetch)
        package["manifest"]["candidate_id"] = "c-002"
        with self.assertRaisesRegex(ValueError, "SEC_ARCHIVE_MANIFEST_HASH_MISMATCH"):
            verify_sec_archive(package, RAW)


if __name__ == "__main__":
    unittest.main()
