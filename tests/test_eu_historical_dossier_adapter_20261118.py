import unittest
from research.eu_historical_dossier_adapter_20261118 import audit_eu_historical_dossier_readiness as audit

class EUHistoricalDossierAdapterTests(unittest.TestCase):
    def test_missing_candidates_blocked(self):
        self.assertEqual(audit({})["blocks"],["HISTORICAL_CANDIDATES_INVALID"])
    def test_historical_usd_close_not_eu_quote(self):
        x=audit({"candidates":[{"symbol":"ASML.AS","last_close_usd":900,"recovery_map":{}}]})
        self.assertIn("EU_QUOTE_UNIT_NOT_ATTESTED",x["rows"][0]["blocks"])
        self.assertFalse(x["rows"][0]["ledger_ready"])
    def test_missing_point_in_time_evidence_explicit(self):
        x=audit({"candidates":[{"symbol":"ASML.AS","market":"EU","quote_currency":"EUR"}]})
        self.assertIn("SOURCE_OBSERVED_UTC_MISSING",x["rows"][0]["blocks"])
        self.assertIn("DECISION_OBSERVED_UTC_MISSING",x["rows"][0]["blocks"])
    def test_gbp_unit_kept_explicit(self):
        x=audit({"candidates":[{"symbol":"ABC.L","market":"EU","quote_currency":"GBp"}]})
        self.assertEqual(x["rows"][0]["quote_unit"],"GBp")
    def test_invalid_symbol_visible(self):
        x=audit({"candidates":[{"symbol":""}]})
        self.assertEqual(x["rows"][0]["blocks"],["SYMBOL_MISSING"])
    def test_claimed_trade_ready_never_inherited(self):
        x=audit({"candidates":[{"symbol":"ASML.AS","trade_ready":True}]})
        self.assertIn("UNVERIFIED_TRADE_READY_CLAIM",x["rows"][0]["blocks"])
        self.assertFalse(x["trade_ready"])
if __name__=="__main__":
    unittest.main()
