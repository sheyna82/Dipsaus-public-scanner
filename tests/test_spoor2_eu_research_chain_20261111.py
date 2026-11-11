import unittest
from datetime import datetime, timezone
from research.spoor2_eu_research_chain_20261111 import evaluate_eu_research_chain
NOW = datetime(2026, 11, 11, 10, tzinfo=timezone.utc)

def sample():
    d=dict(quote_unit="GBp", ask="125.5", target_bid="145", invalidation="120",
           budget_eur="3500", eur_per_base_unit="1.2", buy_fee_eur="3",
           sell_fee_eur="3", buy_fx_rate="0.0025", sell_fx_rate="0.0025")
    for role in ("ask", "target_bid", "invalidation", "fx", "fees"):
        d[role+"_evidence"]=dict(provider_id=role, source_record_id="fixture-"+role,
            source_url="https://example.org/"+role, checked_utc=NOW.isoformat())
    for role in ("ask", "target_bid", "invalidation"):
        d[role+"_evidence"].update(quote_unit="GBp", observed_price=d[role])
    d["fx_evidence"].update(source_currency="GBP", target_currency="EUR", eur_per_base_unit="1.2")
    d["fees_evidence"].update({k:d[k] for k in ("buy_fee_eur","sell_fee_eur","buy_fx_rate","sell_fx_rate")})
    return d

class EuropeanResearchChainTests(unittest.TestCase):
    def test_complete_fixture_is_never_trade_ready(self):
        r=evaluate_eu_research_chain(sample(),now_utc=NOW)
        self.assertEqual(r["status"],"RESEARCH_ONLY")
        self.assertEqual(r["scenario"]["status"],"ILLUSTRATIVE_NOT_VERIFIED")
        self.assertIn("EXTERNAL_SOURCE_ATTESTATION_NOT_CONNECTED",r["blocks"])
        self.assertFalse(r["trade_ready"])
        self.assertFalse(r["order_placement_enabled"])
    def test_evidence_mismatch_does_not_disappear(self):
        d=sample()
        d["ask_evidence"]["observed_price"]="126"
        r=evaluate_eu_research_chain(d,now_utc=NOW)
        self.assertIn("ASK_PRICE_MISMATCH",r["blocks"])
    def test_fee_mismatch_does_not_disappear(self):
        d=sample()
        d["fees_evidence"]["buy_fee_eur"]="0"
        self.assertIn("FEES_MISMATCH",evaluate_eu_research_chain(d,now_utc=NOW)["blocks"])
    def test_missing_inputs_block(self):
        d=sample()
        del d["eur_per_base_unit"]
        r=evaluate_eu_research_chain(d,now_utc=NOW)
        self.assertEqual(r["status"],"BLOCKED")
        self.assertEqual(r["notification_channel"],"NONE")
    def test_bad_price_structure_blocks(self):
        d=sample()
        d["invalidation"]="130"
        r=evaluate_eu_research_chain(d,now_utc=NOW)
        self.assertEqual(r["status"],"BLOCKED")
        self.assertIn("PRICE_STRUCTURE_INVALID",r["blocks"])
    def test_bad_candidate_blocks(self):
        self.assertEqual(evaluate_eu_research_chain(None,now_utc=NOW)["blocks"],["INVALID_CANDIDATE"])

    def test_receipt_present_and_reproducible(self):
        d=sample()
        first=evaluate_eu_research_chain(d,now_utc=NOW)
        second=evaluate_eu_research_chain(d,now_utc=NOW)
        self.assertEqual(first["evidence_receipt"]["status"],"LOCAL_RECEIPT_ONLY")
        self.assertEqual(first["evidence_receipt"]["payload_sha256"],
                         second["evidence_receipt"]["payload_sha256"])
        self.assertFalse(first["trade_ready"])

    def test_receipt_detects_evidence_change(self):
        d=sample()
        first=evaluate_eu_research_chain(d,now_utc=NOW)
        d["ask_evidence"]["source_record_id"]="changed"
        second=evaluate_eu_research_chain(d,now_utc=NOW)
        self.assertNotEqual(first["evidence_receipt"]["payload_sha256"],
                            second["evidence_receipt"]["payload_sha256"])

    def test_noncanonical_input_blocks_before_scenario(self):
        d=sample()
        d["ask_evidence"]["extra_float"]=1.5
        r=evaluate_eu_research_chain(d,now_utc=NOW)
        self.assertEqual(r["status"],"BLOCKED")
        self.assertIn("NONCANONICAL_EVIDENCE",r["blocks"])
        self.assertEqual(r["notification_channel"],"NONE")

    def test_independent_receipt_verification_is_required(self):
        r=evaluate_eu_research_chain(sample(),now_utc=NOW)
        self.assertTrue(r["receipt_verification"]["receipt_verified"])
        self.assertEqual(r["receipt_verification"]["status"],"LOCAL_INTEGRITY_VERIFIED")
        self.assertFalse(r["trade_ready"])

    def test_receipt_verification_never_removes_external_block(self):
        r=evaluate_eu_research_chain(sample(),now_utc=NOW)
        self.assertIn("EXTERNAL_SOURCE_ATTESTATION_NOT_CONNECTED",r["blocks"])
        self.assertEqual(r["notification_channel"],"RESEARCH_PREVIEW_ONLY")
        self.assertFalse(r["order_placement_enabled"])

if __name__=="__main__":
    unittest.main()
