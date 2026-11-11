import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from research_immutable_candidate_registration import register_candidate_once


class ImmutableRegistrationTests(unittest.TestCase):
    def candidate(self):
        return {"symbol": "AMD", "signal_session": "2026-11-02",
                "protocol_id": "research-v1", "future_outcome": None,
                "trade_ready": False}

    def test_exclusive_write_and_digest(self):
        with tempfile.TemporaryDirectory() as tmp:
            instant = lambda: datetime(2026, 11, 3, 15, tzinfo=timezone.utc)
            result = register_candidate_once(self.candidate(), tmp, clock=instant)
            self.assertEqual(result["status"], "created")
            path = Path(result["path"])
            self.assertEqual(path.stem, result["candidate_identity_sha256"])
            saved = json.loads(path.read_text())
            self.assertEqual(saved["registered_at_utc"], "2026-11-03T15:00:00+00:00")
            self.assertFalse(saved["registration_clock_proof_independent"])
            self.assertEqual(register_candidate_once(self.candidate(), tmp, clock=instant)["status"],
                             "duplicate")

    def test_second_registration_with_new_clock_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            first = lambda: datetime(2026, 11, 3, 15, tzinfo=timezone.utc)
            second = lambda: datetime(2026, 11, 3, 16, tzinfo=timezone.utc)
            initial = register_candidate_once(self.candidate(), tmp, clock=first)
            with self.assertRaisesRegex(ValueError, "candidate_already_registered_with_different_payload"):
                register_candidate_once(self.candidate(), tmp, clock=second)
            self.assertEqual(len(list(Path(tmp).glob("*.json"))), 1)
            self.assertEqual(json.loads(Path(initial["path"]).read_text())["registered_at_utc"],
                             "2026-11-03T15:00:00+00:00")

    def test_reject_backdated_caller_registration(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError, "caller_supplied_registration_time_forbidden"):
                register_candidate_once(dict(self.candidate(), registered_at_utc="2020-01-01"), tmp)

    def test_reject_non_utc_clock(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError, "utc_clock_required"):
                register_candidate_once(self.candidate(), tmp,
                    clock=lambda: datetime(2026, 11, 3, tzinfo=timezone(timedelta(hours=1))))

    def test_directory_must_exist(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError, "candidate_directory_must_exist"):
                register_candidate_once(self.candidate(), str(Path(tmp) / "missing"))


if __name__ == "__main__":
    unittest.main()
