import unittest
from research.spoor2_combined_evidence_gate_20261113 import audit_combined_evidence
C={"symbol":"ASML.AS","isin":"NL0010273215","venue_mic":"XAMS",
   "market":"NL","product_type":"EQUITY","trading_currency":"EUR"}
D={"evidence":[{"url":"https://example.org/mic","role":"corroboration"}],
   "instruments":[{"provider_symbol":"ASML.AS","isin":"NL0010273215",
                   "venue_mic_candidate":"XAMS","currency":"EUR"}],"trade_ready":True}
class CombinedEvidenceGateTests(unittest.TestCase):
    def test_matched_still_blocked(self):
        r=audit_combined_evidence(C,D)
        self.assertEqual(r["matching_mic_record_count"],1)
        self.assertFalse(r["trade_ready"])
    def test_mic_mismatch(self):
        self.assertIn("MIC_DOSSIER_INSTRUMENT_MISMATCH",
                      audit_combined_evidence({**C,"venue_mic":"XETR"},D)["blocks"])
    def test_isin_mismatch(self):
        self.assertIn("MIC_DOSSIER_INSTRUMENT_MISMATCH",
                      audit_combined_evidence({**C,"isin":"NL0010273216"},D)["blocks"])
    def test_currency_mismatch(self):
        self.assertIn("MIC_DOSSIER_INSTRUMENT_MISMATCH",
                      audit_combined_evidence({**C,"trading_currency":"USD"},D)["blocks"])
    def test_missing_dossier(self):
        self.assertIn("INVALID_DOSSIER",audit_combined_evidence(C,None)["blocks"])
    def test_fake_fee_claim(self):
        meta={"source_url":"https://example.invalid/claim","retrieved_utc":"2026-11-13T09:00:00Z",
              "source_version":"claim","independent_verification":True}
        r=audit_combined_evidence(C,D,isin_record={**meta,"isin":C["isin"]},
          mic_record={**meta,"venue_mic":"XAMS"},
          listing_record={**meta,**{k:C[k] for k in ("symbol","isin","venue_mic","market")}},
          degiro_record={**meta,**C,"broker":"DEGIRO","tariff_effective_date":"2026-11-13",
                         "tariff_rule_id":"claim"})
        self.assertFalse(r["order_placement_enabled"])
        self.assertFalse(r["degiro_fee_verified"])
