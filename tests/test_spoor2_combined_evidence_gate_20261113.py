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

    def test_duplicate_matching_records_never_authorize(self):
        dossier={**D,"instruments":D["instruments"]*2}
        r=audit_combined_evidence(C,dossier)
        self.assertEqual(r["matching_mic_record_count"],2)
        self.assertIn("MIC_DOSSIER_INSTRUMENT_MISMATCH",r["blocks"])
        self.assertFalse(r["trade_ready"])
    def test_untrusted_documentary_url_never_authorizes(self):
        dossier={**D,"evidence":[{"url":"http://example.org/mic","role":"primary"}]}
        r=audit_combined_evidence(C,dossier)
        self.assertIn("INVALID_DOCUMENTARY_SOURCE",r["blocks"])
        self.assertFalse(r["source_attested"])
    def test_claimant_supplied_source_authority_never_authorizes(self):
        dossier={**D,"source_attested":True,"mic_registered":True,
                 "order_placement_enabled":True,"broker_route_verified":True}
        r=audit_combined_evidence(C,dossier)
        self.assertFalse(r["source_attested"])
        self.assertFalse(r["mic_registered"])
        self.assertFalse(r["order_placement_enabled"])
        self.assertFalse(r["broker_route_verified"])
    def test_missing_candidate_currency_cannot_match(self):
        candidate={k:v for k,v in C.items() if k!="trading_currency"}
        r=audit_combined_evidence(candidate,D)
        self.assertEqual(r["matching_mic_record_count"],0)
        self.assertIn("MIC_DOSSIER_INSTRUMENT_MISMATCH",r["blocks"])
        self.assertFalse(r["trade_ready"])
    def test_matched_operating_mic_never_verifies_execution_segment(self):
        r = audit_combined_evidence(C, D)
        self.assertFalse(r["segment_mic_verified"])
        self.assertFalse(r["mic_documentary"]["segment_mic_verified"])
        self.assertIn("SEGMENT_MIC_NOT_VERIFIED", r["blocks"])
        self.assertFalse(r["trade_ready"])
        self.assertFalse(r["order_placement_enabled"])
