import unittest
from research.spoor2_mic_evidence_gate_20261113 import audit_mic_dossier

class MicEvidenceGateTests(unittest.TestCase):
    def test_untrusted_claim_never_authorizes(self):
        d={"evidence":[{"url":"https://example.org/mic","role":"corroboration"}],
           "instruments":[{"provider_symbol":"ASML.AS","isin":"NL0010273215",
             "venue_mic_candidate":"XAMS","currency":"EUR"}],
           "source_attested":True,"trade_ready":True,"official_iso_register_rows_checked":True}
        r=audit_mic_dossier(d)
        self.assertFalse(r["source_attested"])
        self.assertFalse(r["trade_ready"])
        self.assertIn("ISO_REGISTER_RECORD_NOT_ATTESTED",r["blocks"])
    def test_invalid_mic(self):
        r=audit_mic_dossier({"instruments":[{"provider_symbol":"IFX.DE","isin":"DE0006231004",
             "venue_mic_candidate":"XETRA","currency":"EUR"}]})
        self.assertIn("INVALID_MIC_FORMAT",r["instruments"][0]["blocks"])
    def test_missing_dossier(self):
        self.assertIn("INVALID_DOSSIER",audit_mic_dossier(None)["blocks"])
        self.assertIn("EMPTY_INSTRUMENT_LIST",audit_mic_dossier({"instruments":[]})["blocks"])
    def test_duplicate(self):
        x={"provider_symbol":"RHM.DE","isin":"DE0007030009","venue_mic_candidate":"XETR","currency":"EUR"}
        r=audit_mic_dossier({"instruments":[x,x]})
        self.assertIn("DUPLICATE_INSTRUMENT",r["instruments"][1]["blocks"])
