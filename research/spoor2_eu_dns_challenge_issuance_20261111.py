"""Offline issuance ledger for DNS challenges; never grants DNS admission.

A nonce must be registered as issued before consumption. The issuer identity
is not independently authenticated here. Local SQLite is not distributed.
"""
import sqlite3

def issue_dns_challenge(database_path, *, nonce, issuer_id):
    base={"status":"BLOCKED","issued":False,"issuer_attested":False,
          "dns_admitted":False,"connection_authorized":False,"trade_ready":False}
    if not isinstance(database_path,str) or not database_path.strip() or database_path==":memory:" or database_path.startswith("file:"):
        return {**base,"blocks":["INVALID_ISSUANCE_LEDGER_PATH"]}
    if not isinstance(nonce,str) or not 32<=len(nonce)<=128 or any(c not in "0123456789abcdef" for c in nonce):
        return {**base,"blocks":["INVALID_ISSUANCE_NONCE"]}
    if not isinstance(issuer_id,str) or not issuer_id.strip() or issuer_id.strip()!=issuer_id or len(issuer_id)>200:
        return {**base,"blocks":["INVALID_ISSUER_CLAIM"]}
    try:
        with sqlite3.connect(database_path,timeout=5) as conn:
            conn.execute("CREATE TABLE IF NOT EXISTS issued_dns_challenges (nonce TEXT PRIMARY KEY, issuer_id TEXT NOT NULL)")
            conn.execute("INSERT INTO issued_dns_challenges(nonce,issuer_id) VALUES (?,?)",(nonce,issuer_id))
    except sqlite3.IntegrityError:
        return {**base,"blocks":["NONCE_ALREADY_ISSUED"]}
    except (sqlite3.Error,OSError):
        return {**base,"blocks":["ISSUANCE_LEDGER_UNAVAILABLE"]}
    return {**base,"status":"LOCAL_ISSUANCE_RECORDED_ONLY","issued":True,
            "blocks":["ISSUER_IDENTITY_NOT_ATTESTED","ISSUANCE_AUTHORITY_NOT_VERIFIED",
                      "DNS_EVIDENCE_NOT_ADMITTED"]}

def review_dns_challenge_issuance(database_path, *, nonce):
    base={"status":"BLOCKED","issued":False,"issuer_attested":False,
          "dns_admitted":False,"connection_authorized":False,"trade_ready":False}
    if not isinstance(database_path,str) or not database_path.strip() or database_path==":memory:" or database_path.startswith("file:"):
        return {**base,"blocks":["INVALID_ISSUANCE_LEDGER_PATH"]}
    if not isinstance(nonce,str) or not 32<=len(nonce)<=128 or any(c not in "0123456789abcdef" for c in nonce):
        return {**base,"blocks":["INVALID_ISSUANCE_NONCE"]}
    try:
        with sqlite3.connect(database_path,timeout=5) as conn:
            row=conn.execute("SELECT issuer_id FROM issued_dns_challenges WHERE nonce=?",(nonce,)).fetchone()
    except (sqlite3.Error,OSError):
        return {**base,"blocks":["ISSUANCE_LEDGER_UNAVAILABLE"]}
    if row is None:
        return {**base,"blocks":["CHALLENGE_NOT_ISSUED"]}
    return {**base,"status":"LOCAL_ISSUANCE_RECORD_FOUND_ONLY","issued":True,
            "issuer_identity_claim":row[0],
            "blocks":["ISSUER_IDENTITY_NOT_ATTESTED","ISSUANCE_AUTHORITY_NOT_VERIFIED",
                      "DNS_EVIDENCE_NOT_ADMITTED"]}
