"""Offline DNS evidence admission orchestration: verify before consuming nonce.

No trust anchors are currently approved; no challenge can be consumed or
DNS admitted through this function until independently reviewed policy exists.
"""
from research.spoor2_eu_signed_dns_observation_20261111 import verify_signed_dns_observation
from research.spoor2_eu_dns_challenge_ledger_20261111 import consume_dns_challenge_once
from research.spoor2_eu_dns_challenge_issuance_20261111 import review_dns_challenge_issuance

def review_dns_challenge_admission(database_path, *, issuance_database_path=None, **verification_inputs):
    base={"status":"BLOCKED","consumed":False,"dns_admitted":False,
          "connection_authorized":False,"trade_ready":False,
          "order_placement_enabled":False}
    verification=verify_signed_dns_observation(**verification_inputs)
    if verification.get("signature_verified") is not True:
        return {**base,"blocks":["SIGNATURE_NOT_VERIFIED"],
                "verification_blocks":verification.get("blocks",[])}
    if verification.get("key_trusted") is not True:
        return {**base,"blocks":["SIGNER_NOT_INDEPENDENTLY_TRUSTED"],
                "verification_blocks":verification.get("blocks",[])}
    nonce=verification_inputs.get("challenge_nonce")
    issuance=(review_dns_challenge_issuance(issuance_database_path,nonce=nonce)
              if isinstance(nonce,str) else {"blocks":["INVALID_ISSUANCE_NONCE"]})
    if issuance.get("issued") is not True:
        return {**base,"blocks":["CHALLENGE_ISSUANCE_NOT_VERIFIED"],
                "issuance_blocks":issuance.get("blocks",[])}
    if issuance.get("issuer_attested") is not True:
        return {**base,"blocks":["CHALLENGE_ISSUER_NOT_ATTESTED"],
                "issuance_blocks":issuance.get("blocks",[])}
    digest=verification.get("record_sha256")
    if not isinstance(nonce,str) or not isinstance(digest,str):
        return {**base,"blocks":["INCOMPLETE_VERIFIED_OBSERVATION"]}
    consumed=consume_dns_challenge_once(database_path,nonce=nonce,
                                        observation_sha256=digest)
    if consumed.get("consumed") is not True:
        return {**base,"blocks":["CHALLENGE_CONSUMPTION_FAILED"],
                "ledger_blocks":consumed.get("blocks",[])}
    return {**base,"status":"LOCAL_VERIFIED_CHALLENGE_CONSUMED_ONLY",
            "consumed":True,
            "blocks":["DNSSEC_NOT_VERIFIED","DISTRIBUTED_REPLAY_NOT_VERIFIED",
                      "DNS_EVIDENCE_NOT_ADMITTED"]}
