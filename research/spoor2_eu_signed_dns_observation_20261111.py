"""Offline cryptographic DNS evidence verifier with externally pinned Ed25519 trust key.

A valid signature attests the signer of this record, NOT DNSSEC, DNS truth,
resolver independence, or a live connection. No network or trading operations.
"""
import base64
import hashlib
import json
from datetime import datetime
from research.spoor2_eu_dns_provenance_20261111 import review_dns_provenance
from research.spoor2_eu_dns_signer_trust_anchor_20261111 import review_dns_signer_trust_anchor

def _canonical(record):
    return json.dumps(record,sort_keys=True,separators=(",",":"),ensure_ascii=True).encode("ascii")

def verify_signed_dns_observation(url, *, allowed_hosts, resolved_addresses,
                                  resolver_identity, observation_utc,
                                  signed_record, signature_b64, trusted_public_key_b64,
                                  verification_time_utc, max_age_seconds=300):
    base={"status":"BLOCKED","dnssec_verified":False,"dns_admitted":False,
          "connection_authorized":False,"trade_ready":False,
          "order_placement_enabled":False}
    provenance=review_dns_provenance(url,allowed_hosts=allowed_hosts,
        resolved_addresses=resolved_addresses,resolver_identity=resolver_identity,
        observation_utc=observation_utc)
    if provenance["status"]!="OFFLINE_DNS_PROVENANCE_CLAIMS_ONLY":
        return {**base,"blocks":["INVALID_DNS_PROVENANCE"]}
    if (not isinstance(signed_record,dict) or
        set(signed_record)!=set(provenance["record"]) or
        signed_record!=provenance["record"]):
        return {**base,"blocks":["SIGNED_RECORD_BINDING_MISMATCH"]}
    if type(max_age_seconds) is not int or not 1<=max_age_seconds<=3600:
        return {**base,"blocks":["INVALID_AGE_POLICY"]}
    if not isinstance(verification_time_utc,str):
        return {**base,"blocks":["INVALID_VERIFICATION_TIME"]}
    try:
        now=datetime.fromisoformat(verification_time_utc.replace("Z","+00:00"))
        seen=datetime.fromisoformat(observation_utc.replace("Z","+00:00"))
        if (not isinstance(verification_time_utc,str) or
            not verification_time_utc.endswith("Z") or
            now.tzinfo is None or now.utcoffset().total_seconds()!=0 or
            not 0<=(now-seen).total_seconds()<=max_age_seconds):
            return {**base,"blocks":["DNS_OBSERVATION_OUTSIDE_VALIDITY_WINDOW"]}
    except (ValueError,TypeError,AttributeError):
        return {**base,"blocks":["INVALID_VERIFICATION_TIME"]}
    try:
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
        from cryptography.exceptions import InvalidSignature
    except ImportError:
        return {**base,"blocks":["CRYPTOGRAPHIC_VERIFIER_UNAVAILABLE"]}
    try:
        if not isinstance(signature_b64,str) or not isinstance(trusted_public_key_b64,str):
            raise ValueError("invalid encoding")
        sig=base64.b64decode(signature_b64,validate=True)
        key=base64.b64decode(trusted_public_key_b64,validate=True)
        if len(sig)!=64 or len(key)!=32:
            raise ValueError("invalid key or signature size")
        Ed25519PublicKey.from_public_bytes(key).verify(sig,_canonical(signed_record))
    except (ValueError,TypeError,base64.binascii.Error,InvalidSignature):
        # All malformed or invalid signatures fail closed without exposing data.
        return {**base,"blocks":["INVALID_DNS_OBSERVATION_SIGNATURE"]}
    anchor=review_dns_signer_trust_anchor(trusted_public_key_b64)
    return {**base,"status":"SIGNED_DNS_OBSERVATION_VERIFIED_ONLY",
            "signature_verified":True,"key_trusted":anchor["key_trusted"],
            "dns_admitted":False,
            "blocks":anchor["blocks"]+["TRUST_KEY_PROVENANCE_NOT_INDEPENDENTLY_ATTESTED",
                      "DNSSEC_NOT_VERIFIED","RESOLVER_INDEPENDENCE_NOT_VERIFIED",
                      "NETWORK_CONNECTION_NOT_AUTHORIZED"],
            "record_sha256":hashlib.sha256(_canonical(signed_record)).hexdigest(),
            "scope":"signature over exact DNS claims only; no DNSSEC or live DNS"}
