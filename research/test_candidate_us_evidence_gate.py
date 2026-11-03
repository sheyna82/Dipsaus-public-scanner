"""Offline tests for combined US evidence gate."""
import tempfile
import unittest
from pathlib import Path
from research.candidate_us_offline_capture import archive_capture
from research.candidate_us_evidence_gate import audit_us_batch_evidence


def capture():
    return {"sample_symbols": ["AAA"], "observed_at_utc": "2026-11-03T12:00:00Z",
            "assessments": {"AAA": {"last_bar_date": "2026-11-02",
                                   "drawdown_pct": -10, "rebound_from_low_pct": 4,
                                   "early_turn": False, "established_turn": False,
                                   "signal_count": 1, "signals": {"turn": False},
                                   "pre_screen_match": False}}, "failures": {}}


def provenance():
    return {"AAA": {"provider": "example", "observed_at": "2026-11-02T20:00:00Z",
                    "published_at": "2026-11-02T21:00:00Z",
                    "ingested_at": "2026-11-02T21:05:00Z",
                    "revision_asof": "2026-11-02T21:00:00Z"}}


class EvidenceGateTests(unittest.TestCase):
    def test_valid_metadata_passes_but_not_trade_ready(self):
        item = capture()
        with tempfile.TemporaryDirectory() as directory:
            saved = archive_capture(item, Path(directory))["archive"]
            result = audit_us_batch_evidence(saved["path"], item, provenance(), saved["sha256"])
            self.assertTrue(result["evidence_gate_accepted"])
            self.assertFalse(result["independent_prospective_proof"])
            self.assertFalse(result["trade_ready"])

    def test_future_metadata_fails_gate(self):
        item = capture()
        source = provenance()
        source["AAA"]["published_at"] = "2026-11-04T12:00:00Z"
        with tempfile.TemporaryDirectory() as directory:
            saved = archive_capture(item, Path(directory))["archive"]
            result = audit_us_batch_evidence(saved["path"], item, source, saved["sha256"])
            self.assertFalse(result["evidence_gate_accepted"])

    def test_same_counts_different_symbol_fails(self):
        item = capture()
        with tempfile.TemporaryDirectory() as directory:
            saved = archive_capture(item, Path(directory))["archive"]
            other = capture()
            other["sample_symbols"] = ["BBB"]
            other["assessments"] = {"BBB": other["assessments"].pop("AAA")}
            with self.assertRaisesRegex(ValueError, "ARCHIVE_CAPTURE_SYMBOL_MISMATCH"):
                audit_us_batch_evidence(saved["path"], other, {"BBB": provenance()["AAA"]}, saved["sha256"])


if __name__ == "__main__":
    unittest.main()
