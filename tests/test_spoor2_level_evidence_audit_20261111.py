"""Offline evidence audit regression tests: no live broker or ntfy access."""
import unittest
from datetime import datetime, timezone, timedelta
from research.spoor2_level_evidence_audit_20261111 import audit_levels

NOW = datetime(2026, 11, 11, 10, 0, tzinfo=timezone.utc)


def dossier():
    return {
        "broker_ask_usd": 52.05, "invalidation_usd": 49.0,
        "resistance_usd": 58.20,
        "broker_evidence": {"verified": True, "source": "broker-snapshot",
                            "source_record_id": "broker-001",
                            "checked_utc": NOW.isoformat(), "observed_price_usd": 52.05},
        "invalidation_evidence": {"verified": True, "source": "independent-chart",
                                  "source_record_id": "structure-001",
                                  "checked_utc": NOW.isoformat(), "formed_utc": "2026-11-02T10:00:00+00:00", "structure_still_valid": True, "observed_price_usd": 49.0},
        "resistance_evidence": {"verified": True, "source": "independent-chart",
                                "source_record_id": "resistance-001",
                                "checked_utc": NOW.isoformat(), "formed_utc": "2026-11-03T10:00:00+00:00", "structure_still_valid": True, "observed_price_usd": 58.20},
    }


class EvidenceAuditTests(unittest.TestCase):
    def test_complete_provenance_never_auto_approves(self):
        result = audit_levels(dossier(), now_utc=NOW)
        self.assertEqual(result["status"], "EVIDENCE_PRESENT_REQUIRES_INDEPENDENT_REVIEW")
        self.assertGreaterEqual(result["reference_rr"], 2)
        self.assertFalse(result["trade_ready"])

    def test_missing_and_unverified_evidence_blocks(self):
        for label in ("broker", "invalidation", "resistance"):
            row = dossier()
            del row[label + "_evidence"]
            self.assertEqual(audit_levels(row, now_utc=NOW)["status"], "BLOCKED")
            row = dossier()
            row[label + "_evidence"]["verified"] = "true"
            self.assertEqual(audit_levels(row, now_utc=NOW)["status"], "BLOCKED")

    def test_stale_future_and_untraceable_block(self):
        for delta in (-901, 1):
            row = dossier()
            row["broker_evidence"]["checked_utc"] = (NOW + timedelta(seconds=delta)).isoformat()
            self.assertEqual(audit_levels(row, now_utc=NOW)["status"], "BLOCKED")
        row = dossier()
        row["resistance_evidence"]["source_record_id"] = ""
        self.assertEqual(audit_levels(row, now_utc=NOW)["status"], "BLOCKED")

    def test_historical_structure_can_be_old_but_must_be_revalidated(self):
        row = dossier()
        row["resistance_evidence"]["checked_utc"] = (NOW - timedelta(hours=12)).isoformat()
        self.assertEqual(audit_levels(row, now_utc=NOW)["status"],
                         "EVIDENCE_PRESENT_REQUIRES_INDEPENDENT_REVIEW")
        row["resistance_evidence"]["structure_still_valid"] = False
        self.assertIn("RESISTANCE_STRUCTURE_NOT_REVALIDATED",
                      audit_levels(row, now_utc=NOW)["blocks"])

    def test_mismatched_price_blocks(self):
        row = dossier()
        row["resistance_evidence"]["observed_price_usd"] = 57
        self.assertIn("RESISTANCE_PRICE_MISMATCH", audit_levels(row, now_utc=NOW)["blocks"])

    def test_insufficient_rr_blocks(self):
        row = dossier()
        row["resistance_usd"] = 55
        row["resistance_evidence"]["observed_price_usd"] = 55
        self.assertIn("RR_BELOW_TWO", audit_levels(row, now_utc=NOW)["blocks"])

    def test_invalid_inputs_fail_closed(self):
        self.assertEqual(audit_levels({}, now_utc=NOW)["status"], "BLOCKED")
        self.assertEqual(audit_levels(dossier(), now_utc=NOW.replace(tzinfo=None))["status"], "BLOCKED")


if __name__ == "__main__":
    unittest.main()
