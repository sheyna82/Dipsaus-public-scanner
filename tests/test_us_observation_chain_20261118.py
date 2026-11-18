"""Synthetic-only provenance chain regression tests."""
import unittest
from research.us_observation_chain_20261118 import append_observation, verify_chain

def obs(t, price=101):
    return {"symbol": "SYNTH", "source_id": "synthetic-fixture",
            "observed_utc": t, "close_usd": price}

A = "2026-11-17T21:00:00Z"
B = "2026-11-17T22:00:00Z"

class ObservationChainTests(unittest.TestCase):
    def test_empty_chain_valid(self):
        self.assertEqual(verify_chain([])["status"], "VALID")

    def test_append_one(self):
        x = append_observation([], obs(A))
        self.assertEqual(x["status"], "VALID")
        self.assertEqual(verify_chain(x["chain"])["count"], 1)
        self.assertFalse(x["trade_ready"])

    def test_append_two(self):
        first = append_observation([], obs(A))["chain"]
        second = append_observation(first, obs(B, 102))
        self.assertEqual(verify_chain(second["chain"])["count"], 2)

    def test_tamper_price_detected(self):
        chain = append_observation([], obs(A))["chain"]
        chain[0]["close_usd"] = 999
        self.assertEqual(verify_chain(chain)["status"], "BLOCKED")

    def test_tamper_timestamp_detected(self):
        chain = append_observation([], obs(A))["chain"]
        chain[0]["observed_utc"] = B
        self.assertEqual(verify_chain(chain)["status"], "BLOCKED")

    def test_duplicate_time_blocked(self):
        chain = append_observation([], obs(A))["chain"]
        self.assertEqual(append_observation(chain, obs(A))["status"], "BLOCKED")

    def test_backwards_time_blocked(self):
        chain = append_observation([], obs(B))["chain"]
        self.assertEqual(append_observation(chain, obs(A))["status"], "BLOCKED")

    def test_missing_source_blocked(self):
        item = obs(A)
        item.pop("source_id")
        self.assertEqual(append_observation([], item)["status"], "BLOCKED")

    def test_invalid_price_blocked(self):
        self.assertEqual(append_observation([], obs(A, -1))["status"], "BLOCKED")

    def test_no_raw_payload_leak(self):
        item = obs(A)
        item["secret_token"] = "DO_NOT_COPY"
        chain = append_observation([], item)["chain"]
        self.assertNotIn("secret_token", chain[0])

    def test_chain_rejects_extra_field(self):
        chain = append_observation([], obs(A))["chain"]
        chain[0]["secret_token"] = "DO_NOT_COPY"
        self.assertEqual(verify_chain(chain)["status"], "BLOCKED")

    def test_chain_rejects_symbol_change(self):
        chain = append_observation([], obs(A))["chain"]
        item = obs(B)
        item["symbol"] = "OTHER"
        self.assertEqual(append_observation(chain, item)["status"], "BLOCKED")

    def test_prior_tamper_prevents_append(self):
        chain = append_observation([], obs(A))["chain"]
        chain[0]["close_usd"] = 9
        self.assertEqual(append_observation(chain, obs(B))["status"], "BLOCKED")

    def test_naive_time_blocked(self):
        self.assertEqual(append_observation([], obs("2026-11-17T21:00:00"))["status"], "BLOCKED")

    def test_boolean_price_blocked(self):
        self.assertEqual(append_observation([], obs(A, True))["status"], "BLOCKED")

if __name__ == "__main__":
    unittest.main()
