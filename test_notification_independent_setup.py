"""Research-branch regression tests: verified independent setup lifecycle.

Uses fake sender/store; never contacts ntfy or brokers.
"""
import unittest
from private_notifications import notify


class Store:
    def require_exclusive_sender(self):
        pass

    def save(self, state):
        pass


def candidate(**extra):
    row = dict(symbol="CSGP", market="US", watch_type="AUTO-US-DISCOVERY",
               status="DEGIRO-VERIFY-NOW", phone_notification_eligible=True,
               provider_freshness_pass=True, structure_available=True,
               intraday_hold_confirmed=True, early_turn_observed=True,
               prealert_trigger_observed=True, breakout_observed=True,
               hold_observed=True, provider_quote=31.07)
    row.update(extra)
    return row


class IndependentSetupLifecycleTest(unittest.TestCase):
    def test_new_verified_setup_realerts_same_phase(self):
        sent = []
        state = {"signals": {}}
        send = lambda symbol, body: sent.append((symbol, body))
        notify(Store(), state, [candidate(verified_setup_id="CSGP-20261102-A")], [], send)
        notify(Store(), state, [candidate(verified_setup_id="CSGP-20261102-A")], [], send)
        notify(Store(), state, [candidate(verified_setup_id="CSGP-20261103-B")], [], send)
        self.assertEqual(len(sent), 2)

    def test_unverified_setup_label_cannot_bypass_legacy_dedupe(self):
        sent = []
        state = {"signals": {}}
        send = lambda symbol, body: sent.append((symbol, body))
        notify(Store(), state, [candidate()], [], send)
        notify(Store(), state, [candidate(verified_setup_id="bad|unverified")], [], send)
        self.assertEqual(len(sent), 1)

    def test_stale_or_unconfirmed_new_setup_remains_silent(self):
        sent = []
        state = {"signals": {}}
        send = lambda symbol, body: sent.append((symbol, body))
        notify(Store(), state, [candidate(verified_setup_id="A", provider_freshness_pass=False)], [], send)
        notify(Store(), state, [candidate(verified_setup_id="B", intraday_hold_confirmed=False)], [], send)
        self.assertEqual(sent, [])


if __name__ == "__main__":
    unittest.main()
