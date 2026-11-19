"""Offline, transactional single-use DNS challenge ledger.

Local SQLite uniqueness is not distributed replay protection. Call only after
cryptographic signature and trust policy checks. Never authorizes DNS or trades.
"""
import hashlib
import sqlite3

def consume_dns_challenge_once(database_path, *, nonce, observation_sha256):
    base={"status":"BLOCKED","consumed":False,"dns_admitted":False,
          "connection_authorized":False,"trade_ready":False,
          "order_placement_enabled":False}
    if (not isinstance(database_path,str) or not database_path.strip()
        or database_path==":memory:" or database_path.startswith("file:")):
        return {**base,"blocks":["INVALID_PERSISTENT_LEDGER_PATH"]}
    if (not isinstance(nonce,str) or not 32<=len(nonce)<=128 or
        any(c not in "0123456789abcdef" for c in nonce)):
        return {**base,"blocks":["INVALID_CHALLENGE_NONCE"]}
    if (not isinstance(observation_sha256,str) or len(observation_sha256)!=64
        or any(c not in "0123456789abcdef" for c in observation_sha256)):
        return {**base,"blocks":["INVALID_OBSERVATION_DIGEST"]}
    try:
        with sqlite3.connect(database_path,timeout=5) as conn:
            conn.execute("CREATE TABLE IF NOT EXISTS consumed_challenges "
                         "(nonce TEXT PRIMARY KEY, observation_sha256 TEXT NOT NULL)")
            conn.execute("INSERT INTO consumed_challenges(nonce,observation_sha256) VALUES (?,?)",
                         (nonce,observation_sha256))
    except sqlite3.IntegrityError:
        return {**base,"blocks":["DNS_CHALLENGE_ALREADY_CONSUMED"]}
    except (sqlite3.Error,OSError):
        return {**base,"blocks":["DNS_CHALLENGE_LEDGER_UNAVAILABLE"]}
    return {**base,"status":"LOCAL_CHALLENGE_CONSUMED_ONLY","consumed":True,
            "blocks":["SIGNATURE_AND_TRUST_NOT_VERIFIED_BY_LEDGER",
                      "DISTRIBUTED_REPLAY_PROTECTION_NOT_ESTABLISHED",
                      "DNS_EVIDENCE_NOT_ADMITTED"]}
