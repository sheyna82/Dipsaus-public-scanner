"""Offline tests for documentary leads; no network or trust promotion."""
import unittest
from research.spoor2_eu_pilot_primary_source_dossier_20261118 import build_primary_source_lead_report


class IssuerLeadTests(unittest.TestCase):
    def test_four_unique_pilots(self):
        report = build_primary_source_lead_report()
        self.assertEqual(len(report["rows"]), 4)
        self.assertEqual(len({r["isin_claim"] for r in report["rows"]}), 4)

    def test_all_sources_are_documentary_only(self):
        report = build_primary_source_lead_report()
        self.assertFalse(report["fresh_external_artifact_capture"])
        for row in report["rows"]:
            self.assertTrue(row["issuer_url"].startswith("https://"))
            self.assertEqual(row["evidence_class"], "UNATTESTED_PUBLIC_ISSUER_PAGE_POINTER")
            for gate in ("source_attested", "instrument_segment_verified",
                         "segment_mic_verified", "broker_route_verified",
                         "degiro_fee_verified", "trade_ready",
                         "order_placement_enabled"):
                self.assertIs(row[gate], False)

    def test_only_explicit_mic_mentions_are_marked(self):
        rows = {r["symbol_claim"]: r for r in build_primary_source_lead_report()["rows"]}
        self.assertFalse(rows["ASML.AS"]["mic_directly_stated_in_issuer_document"])
        self.assertFalse(rows["IFX.DE"]["mic_directly_stated_in_issuer_document"])
        self.assertTrue(rows["NOKIA.HE"]["mic_directly_stated_in_issuer_document"])
        self.assertTrue(rows["RHM.DE"]["mic_directly_stated_in_issuer_document"])


if __name__ == "__main__":
    unittest.main()
