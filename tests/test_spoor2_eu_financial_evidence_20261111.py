import unittest
from datetime import datetime, timezone
from research.spoor2_eu_financial_evidence_20261111 import audit_eu_financial_inputs
NOW = datetime(2026, 11, 11, 10, tzinfo=timezone.utc)

def sample():
    data = dict(quote_unit="GBp", ask="125.5", target_bid="145", invalidation="120",
                eur_per_base_unit="1.2", buy_fee_eur="3", sell_fee_eur="3",
                buy_fx_rate="0.0025", sell_fx_rate="0.0025")
    for role in ("ask", "target_bid", "invalidation", "fx", "fees"):
        data[role + "_evidence"] = dict(provider_id=role, source_record_id="fixture-"+role,
            source_url="https://example.org/"+role, checked_utc=NOW.isoformat())
    for role in ("ask", "target_bid", "invalidation"):
        data[role+"_evidence"].update(quote_unit="GBp", observed_price=data[role])
    data["fx_evidence"].update(source_currency="GBP", target_currency="EUR", eur_per_base_unit="1.2")
    data["fees_evidence"].update({k: data[k] for k in ("buy_fee_eur", "sell_fee_eur", "buy_fx_rate", "sell_fx_rate")})
    return data

class EuropeanFinancialEvidenceTests(unittest.TestCase):
    def test_complete_fixture_still_not_attested(self):
        r = audit_eu_financial_inputs(sample(), now_utc=NOW)
        self.assertEqual(r["blocks"], ["EXTERNAL_SOURCE_ATTESTATION_NOT_CONNECTED"])
        self.assertFalse(r["trade_ready"])
    def test_pence_pounds_fx_pair(self):
        data=sample()
        data["fx_evidence"]["source_currency"]="GBp"
        self.assertIn("FX_PAIR_MISMATCH", audit_eu_financial_inputs(data, now_utc=NOW)["blocks"])
    def test_quote_unit_mismatch(self):
        data=sample()
        data["ask_evidence"]["quote_unit"]="GBP"
        self.assertIn("ASK_UNIT_MISMATCH", audit_eu_financial_inputs(data, now_utc=NOW)["blocks"])
    def test_price_mismatch(self):
        data=sample()
        data["ask_evidence"]["observed_price"]="126"
        self.assertIn("ASK_PRICE_MISMATCH", audit_eu_financial_inputs(data, now_utc=NOW)["blocks"])
    def test_fee_mismatch(self):
        data=sample()
        data["fees_evidence"]["buy_fx_rate"]="0.005"
        self.assertIn("FEES_MISMATCH", audit_eu_financial_inputs(data, now_utc=NOW)["blocks"])
    def test_stale_quote(self):
        data=sample()
        data["ask_evidence"]["checked_utc"]="2026-11-10T10:00:00Z"
        self.assertIn("ASK_STALE_OR_FUTURE", audit_eu_financial_inputs(data, now_utc=NOW)["blocks"])
    def test_missing_provenance(self):
        data=sample()
        data["fx_evidence"].pop("source_record_id")
        self.assertIn("FX_PROVENANCE_INCOMPLETE", audit_eu_financial_inputs(data, now_utc=NOW)["blocks"])
    def test_invalid_inputs(self):
        self.assertEqual(audit_eu_financial_inputs(None, now_utc=NOW)["blocks"], ["INVALID_INPUT"])

if __name__ == "__main__":
    unittest.main()
