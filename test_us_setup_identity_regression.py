"""Research-only regression tests for independent US setup notification identity.

No network calls, real ntfy delivery, broker actions, or production configuration.
"""
import copy
import unittest

from private_notifications import notify


class FakeStore:
    def __init__(self):
        self.snapshots = []

    def require_exclusive_sender(self):
        return None

    def save(self, state):
        self.snapshots.append(copy.deepcopy(state))


def candidate(**changes):
    row = {
        "symbol": "CSGP", "market": "US", "watch_type": "AUTO-US-DISCOVERY",
        "prealert_trigger_observed": True, "phone_notification_eligible": True,
        "provider_freshness_pass": True, "structure_available": True,
        "intraday_hold_confirmed": True, "breakout_observed": True,
        "provider_quote": 31.0,
    }
    row.update(changes)
    return row


class IndependentSetupNotificationTests(unittest.TestCase):
    def setUp(self):
        self.store = FakeStore()
        self.state = {"signals": {}}
        self.sent = []
        self.sender = lambda symbol, body: self.sent.append((symbol, body))

    def push(self, **changes):
        notify(self.store, self.state, [candidate(**changes)], [], self.sender)

    def test_same_setup_same_phase_deduplicates(self):
        self.push(verified_setup_id="structure_A", independent_setup_verified=True)
        self.push(verified_setup_id="structure_A", independent_setup_verified=True)
        self.assertEqual(len(self.sent), 1)

    def test_same_setup_higher_phase_notifies(self):
        self.push(verified_setup_id="structure_A", independent_setup_verified=True)
        self.push(verified_setup_id="structure_A", independent_setup_verified=True,
                  execution_near=True)
        self.assertEqual(len(self.sent), 2)

    def test_independent_setup_same_phase_notifies(self):
        self.push(verified_setup_id="structure_A", independent_setup_verified=True)
        self.push(verified_setup_id="structure_B", independent_setup_verified=True)
        self.assertEqual(len(self.sent), 2)

    def test_unverified_new_setup_does_not_bypass_legacy_dedupe(self):
        self.push(verified_setup_id="structure_A", independent_setup_verified=False)
        self.push(verified_setup_id="structure_B", independent_setup_verified=False)
        self.assertEqual(len(self.sent), 1)

    def test_invalid_setup_identifier_falls_back_to_legacy(self):
        self.push(verified_setup_id="../unsafe", independent_setup_verified=True)
        self.push(verified_setup_id="../different", independent_setup_verified=True)
        self.assertEqual(len(self.sent), 1)

    def test_stale_or_missing_structure_never_notifies(self):
        self.push(verified_setup_id="structure_A", independent_setup_verified=True,
                  provider_freshness_pass=False)
        self.push(verified_setup_id="structure_A", independent_setup_verified=True,
                  structure_available=False)
        self.assertEqual(self.sent, [])

    def test_uncertain_delivery_is_not_retried_after_restart(self):
        def timeout(*args):
            raise TimeoutError("simulated")
        with self.assertRaises(TimeoutError):
            notify(self.store, self.state,
                   [candidate(verified_setup_id="structure_A",
                              independent_setup_verified=True)], [], timeout)
        restored = copy.deepcopy(self.store.snapshots[-1])
        notify(FakeStore(), restored,
               [candidate(verified_setup_id="structure_A",
                          independent_setup_verified=True)], [], self.sender)
        self.assertEqual(self.sent, [])
        self.assertEqual(restored["signals"]["ENTRY|US|CSGP|SETUP|structure_A|PHASE"]["delivery"],
                         "uncertain")


if __name__ == "__main__":
    unittest.main()
