import unittest
from research.spoor2_iso_mic_release_gate_20261113 import audit_iso_mic_release


class IsoMicReleaseGateTests(unittest.TestCase):
    def check(self, as_of, publication="2026-11-09", effective="2026-11-23", **kw):
        return audit_iso_mic_release(
            publication_date=publication, implementation_date=effective,
            as_of_date=as_of, **kw)

    def test_before_publication(self):
        self.assertIn("RELEASE_NOT_YET_PUBLISHED",
                      self.check("2026-11-08")["blocks"])

    def test_published_not_yet_effective(self):
        r = self.check("2026-11-13")
        self.assertIn("RELEASE_CHANGES_NOT_YET_EFFECTIVE", r["blocks"])
        self.assertFalse(r["mic_registered"])

    def test_effective_day_still_not_attested(self):
        r = self.check("2026-11-23", dataset_sha256="a" * 64,
                       parsed_mic_records=[{"mic": "XAMS"}])
        self.assertNotIn("RELEASE_CHANGES_NOT_YET_EFFECTIVE", r["blocks"])
        self.assertIn("OFFICIAL_DATASET_ORIGIN_NOT_ATTESTED", r["blocks"])
        self.assertFalse(r["trade_ready"])

    def test_invalid_date(self):
        self.assertIn("INVALID_RELEASE_DATE",
                      self.check("2026-11-31")["blocks"])

    def test_noncanonical_date(self):
        self.assertIn("INVALID_RELEASE_DATE",
                      self.check("2026-11-3")["blocks"])

    def test_implementation_before_publication(self):
        self.assertIn("IMPLEMENTATION_BEFORE_PUBLICATION",
                      self.check("2026-11-24", effective="2026-11-01")["blocks"])

    def test_forged_digest_cannot_attest(self):
        r = self.check("2026-12-01", dataset_sha256="0" * 64)
        self.assertFalse(r["source_attested"])
        self.assertFalse(r["order_placement_enabled"])

    def test_invalid_digest(self):
        self.assertIn("OFFICIAL_DATASET_DIGEST_MISSING",
                      self.check("2026-12-01", dataset_sha256="Z" * 64)["blocks"])

    def test_invalid_parsed_records(self):
        self.assertIn("INVALID_PARSED_MIC_RECORDS",
                      self.check("2026-12-01", parsed_mic_records={})["blocks"])
