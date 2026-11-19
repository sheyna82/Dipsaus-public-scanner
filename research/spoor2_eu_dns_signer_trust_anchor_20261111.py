"""Offline trust-anchor policy: no DNS signing keys are approved by default.

Pins must be provisioned via independently reviewed repository policy,
not supplied by the DNS evidence producer or request caller.
"""
import base64
import hashlib

# Deliberately empty until a separate trust-key provenance review.
APPROVED_DNS_SIGNER_KEY_SHA256=frozenset()

def review_dns_signer_trust_anchor(public_key_b64):
    base={"status":"BLOCKED","key_trusted":False,"dns_admitted":False,
          "connection_authorized":False,"trade_ready":False,
          "order_placement_enabled":False}
    if not isinstance(public_key_b64,str):
        return {**base,"blocks":["INVALID_SIGNER_PUBLIC_KEY"]}
    try:
        key=base64.b64decode(public_key_b64,validate=True)
    except (ValueError,base64.binascii.Error):
        return {**base,"blocks":["INVALID_SIGNER_PUBLIC_KEY"]}
    if len(key)!=32:
        return {**base,"blocks":["INVALID_SIGNER_PUBLIC_KEY"]}
    fingerprint=hashlib.sha256(key).hexdigest()
    if fingerprint not in APPROVED_DNS_SIGNER_KEY_SHA256:
        return {**base,"blocks":["SIGNER_KEY_NOT_INDEPENDENTLY_APPROVED"],
                "key_sha256":fingerprint}
    # A future approval alone would still not prove DNSSEC or DNS truth.
    return {**base,"status":"SIGNER_KEY_PIN_MATCH_ONLY",
            "key_trusted":True,"dns_admitted":False,
            "blocks":["DNSSEC_NOT_VERIFIED","DNS_EVIDENCE_NOT_ADMITTED"],
            "key_sha256":fingerprint}
