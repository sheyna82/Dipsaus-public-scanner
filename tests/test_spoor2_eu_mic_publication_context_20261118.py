"""Offline tests: MIC publication dates and venue context cannot unlock trades."""
import unittest
from research.spoor2_eu_mic_publication_context_20261118 import build_mic_publication_context


class MicPublicationContextTests(unittest.TestCase):
    def test_november_changes_not_yet_effective_on_november_18(self):
        r = build_mic_publication_context("2026-11-18")
        self.assertEqual(r["iso_publication_date"], "2026-11-09")
        self.assertEqual(r["iso_modifications_effective_date"], "2026-11-23")
        self.assertEqual(len(r["rows"]), 4)
        self.assertTrue(all(not x["november_changes_effective_as_of_date"] for x in r["rows"]))

    def test_implementation_date_does_not_promote_attestation(self):
        r = build_mic_publication_context("2026-11-23")
        self.assertTrue(all(x["november_changes_effective_as_of_date"] for x in r["rows"]))
        self.assertFalse(r["source_attested"])
        self.assertFalse(r["trade_ready"])
        self.assertTrue(all(not x["mic_registry_record_attested"] for x in r["rows"]))

    def test_market_context_not_instrument_proof(self):
        r = build_mic_publication_context()
        self.assertEqual({x["operating_mic_claim"] for x in r["rows"]}, {"XAMS", "XETR", "XHEL"})
        for x in r["rows"]:
            self.assertFalse(x["instrument_listing_attested"])
            self.assertFalse(x["segment_mic_attested"])
        for flag in ("source_attested", "instrument_segment_verified",
                     "segment_mic_verified", "broker_route_verified",
                     "degiro_fee_verified", "trade_ready",
                     "order_placement_enabled", "automatic_orders", "notify"):
            self.assertFalse(r[flag])

    def test_before_publication_is_blocked(self):
        r = build_mic_publication_context("2026-11-08")
        self.assertEqual(r["blocks"], ["MIC_EDITION_NOT_YET_PUBLISHED"])
        self.assertEqual(r["rows"], [])

    def test_bad_date_fails_closed(self):
        r = build_mic_publication_context("tomorrow")
        self.assertEqual(r["blocks"], ["INVALID_OBSERVATION_DATE"])
        self.assertFalse(r["trade_ready"])


if __name__ == "__main__":
    unittest.main()
