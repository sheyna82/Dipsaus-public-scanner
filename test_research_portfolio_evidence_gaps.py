import unittest
from datetime import datetime, timezone
from research_portfolio_evidence_gaps import portfolio_evidence_gap_report

NOW = datetime(2026, 11, 5, 12, tzinfo=timezone.utc)
CONFIG = {"positions": {"RENK": {"status": "PROFIT-WATCH-DYNAMIC", "shares": 50},
                        "ALFEN.AS": {"status": "PROFIT-WATCH-DYNAMIC", "shares": 25},
                        "EXE": {"status": "CLOSED-SWING", "shares": 114}}}

def evidence():
    return {"source": "DEGIRO_EXPORT", "account_scope": "example",
            "captured_at_utc": "2026-11-05T11:30:00Z",
            "positions": {"RENK": 50, "ALFEN": 25, "FER": 71},
            "open_orders": [{"symbol": "RENK", "side": "SELL", "remaining_quantity": 50}],
            "positions_complete": True, "orders_complete": True}

class PortfolioEvidenceGapTests(unittest.TestCase):
    def test_complete_claim_still_exposes_authentication_cash_and_mismatches(self):
        report = portfolio_evidence_gap_report(CONFIG, evidence(), now_utc=NOW)
        codes = report["gap_codes"]
        for code in ("UNAUTHENTICATED_SOURCE", "UNVERIFIED_COMPLETENESS",
                     "POSITION_MISMATCH", "SYMBOL_ALIAS_REVIEW",
                     "CASH_NOT_VERIFIED", "OPEN_ORDERS_REQUIRE_REVIEW"):
            self.assertIn(code, codes)
        self.assertFalse(report["capacity_usable"])
        self.assertFalse(report["trade_ready"])

    def test_partial_and_stale_claims_are_explicit(self):
        record = evidence()
        record["positions_complete"] = False
        record["orders_complete"] = False
        record["captured_at_utc"] = "2026-11-03T11:30:00Z"
        report = portfolio_evidence_gap_report(CONFIG, record, now_utc=NOW)
        for code in ("STALE_BROKER_EVIDENCE", "INCOMPLETE_POSITIONS",
                     "INCOMPLETE_OPEN_ORDERS"):
            self.assertIn(code, report["gap_codes"])

    def test_no_open_orders_still_does_not_establish_cash(self):
        record = evidence()
        record["open_orders"] = []
        record["positions"] = {"RENK": 50, "ALFEN.AS": 25}
        report = portfolio_evidence_gap_report(CONFIG, record, now_utc=NOW)
        self.assertNotIn("OPEN_ORDERS_REQUIRE_REVIEW", report["gap_codes"])
        self.assertIn("CASH_NOT_VERIFIED", report["gap_codes"])
        self.assertFalse(report["capacity_usable"])

    def test_invalid_broker_data_rejected_before_diagnostics(self):
        record = evidence()
        record["positions"] = {None: 25}
        with self.assertRaisesRegex(ValueError, "INVALID_POSITION"):
            portfolio_evidence_gap_report(CONFIG, record, now_utc=NOW)

if __name__ == "__main__":
    unittest.main()
