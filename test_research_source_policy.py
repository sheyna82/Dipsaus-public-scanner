"""Offline provenance classification tests, no network or broker credentials."""
import unittest
from research_source_policy import assess_provenance_claims, classify_source


class SourcePolicyTests(unittest.TestCase):
    def setUp(self):
        self.att = {group: {"source_id": source}
                    for group, source in (
                        ("broker_quote", "degiro-quote"),
                        ("fees", "degiro-fees"),
                        ("technical_levels", "technical-research"),
                        ("fx", "fx-provider"),
                        ("slippage", "slippage-model"))}
        self.registry = {
            "degiro-quote": {"kind": "BROKER"},
            "degiro-fees": {"kind": "BROKER"},
            "technical-research": {"kind": "MANUAL_RESEARCH"},
            "fx-provider": {"kind": "PUBLIC_PROVIDER"},
            "slippage-model": {"kind": "MANUAL_RESEARCH"}}

    def check(self):
        return assess_provenance_claims(self.att, self.registry)

    def test_consistent_claims_still_not_authenticated(self):
        r = self.check()
        self.assertEqual(r["status"], "PROVENANCE_CLAIMS_CONSISTENT")
        self.assertFalse(r["source_authenticity_independently_verified"])
        self.assertFalse(r["trade_ready"])

    def test_yahoo_cannot_be_broker_quote(self):
        self.registry["degiro-quote"] = {
            "kind": "BROKER", "url": "https://query1.finance.yahoo.com/v8/finance/chart/ASML"}
        self.assertEqual(self.check()["reason"], "NOT_BROKER_EVIDENCE")

    def test_yahoo_cannot_be_fee_source(self):
        self.registry["degiro-fees"] = {
            "kind": "BROKER", "url": "https://query2.finance.yahoo.com/x"}
        self.assertEqual(self.check()["reason"], "NOT_BROKER_EVIDENCE")

    def test_missing_broker_source_blocked(self):
        del self.registry["degiro-quote"]
        self.assertEqual(self.check()["reason"], "UNKNOWN_SOURCE")

    def test_broker_quote_not_technical_attestation(self):
        self.registry["technical-research"] = {"kind": "BROKER"}
        self.assertEqual(self.check()["reason"], "TECHNICAL_LEVELS_NOT_INDEPENDENT")

    def test_insecure_url_blocked(self):
        self.assertEqual(classify_source({"kind": "BROKER", "url": "http://example.com"}), "UNKNOWN")

    def test_unknown_kind_blocked(self):
        self.assertEqual(classify_source({"kind": "SECRET", "url": "https://example.com"}), "UNKNOWN")

    def test_public_source_not_independent_broker(self):
        self.registry["degiro-quote"] = {"kind": "PUBLIC_PROVIDER"}
        self.assertEqual(self.check()["reason"], "NOT_BROKER_EVIDENCE")


if __name__ == "__main__":
    unittest.main()
