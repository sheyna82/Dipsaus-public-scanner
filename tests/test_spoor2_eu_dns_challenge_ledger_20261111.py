import os
import sqlite3
import tempfile
import unittest
from research.spoor2_eu_dns_challenge_ledger_20261111 import consume_dns_challenge_once

class ChallengeLedgerTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.db=os.path.join(self.temp.name,"challenges.sqlite3")
        self.args=dict(database_path=self.db,nonce="a"*64,observation_sha256="b"*64)
    def test_first_use_consumes_but_never_admits(self):
        r=consume_dns_challenge_once(**self.args)
        self.assertTrue(r["consumed"])
        self.assertFalse(r["dns_admitted"])
        self.assertFalse(r["trade_ready"])
    def test_replay_rejected_even_with_other_digest(self):
        consume_dns_challenge_once(**self.args)
        r=consume_dns_challenge_once(**{**self.args,"observation_sha256":"c"*64})
        self.assertEqual(r["blocks"],["DNS_CHALLENGE_ALREADY_CONSUMED"])
    def test_replay_rejected_after_reopen(self):
        consume_dns_challenge_once(**self.args)
        r=consume_dns_challenge_once(**self.args)
        self.assertEqual(r["blocks"],["DNS_CHALLENGE_ALREADY_CONSUMED"])
    def test_invalid_nonce_never_creates_database(self):
        r=consume_dns_challenge_once(**{**self.args,"nonce":"bad"})
        self.assertEqual(r["blocks"],["INVALID_CHALLENGE_NONCE"])
        self.assertFalse(os.path.exists(self.db))
    def test_memory_database_not_accepted(self):
        r=consume_dns_challenge_once(**{**self.args,"database_path":":memory:"})
        self.assertEqual(r["blocks"],["INVALID_PERSISTENT_LEDGER_PATH"])
    def test_broken_database_fails_closed(self):
        with open(self.db,"wb") as f: f.write(b"not a sqlite database")
        r=consume_dns_challenge_once(**self.args)
        self.assertEqual(r["blocks"],["DNS_CHALLENGE_LEDGER_UNAVAILABLE"])
if __name__=="__main__": unittest.main()
