"""Fail-closed offline admission for DNS provenance evidence.

No caller-provided signature, timestamp or DNSSEC claim establishes trust.
External cryptographic verification is deliberately not implemented here.
"""
from research.spoor2_eu_dns_provenance_20261111 import review_dns_provenance

def review_dns_evidence_admission(url, *, allowed_hosts, resolved_addresses,
                                  resolver_identity, observation_utc,
                                  evidence=None):
    base={"status":"BLOCKED","dns_admitted":False,"connection_authorized":False,
          "trade_ready":False,"order_placement_enabled":False}
    provenance=review_dns_provenance(
        url,allowed_hosts=allowed_hosts,resolved_addresses=resolved_addresses,
        resolver_identity=resolver_identity,observation_utc=observation_utc)
    if provenance["status"]!="OFFLINE_DNS_PROVENANCE_CLAIMS_ONLY":
        return {**base,"blocks":["INVALID_DNS_PROVENANCE"]}
    if evidence is None:
        return {**base,"blocks":["MISSING_EXTERNAL_DNS_EVIDENCE"],
                "record_sha256":provenance["record_sha256"]}
    if not isinstance(evidence,dict):
        return {**base,"blocks":["INVALID_EXTERNAL_DNS_EVIDENCE"]}
    required=("resolver_signature","resolver_public_key","signed_response",
              "verification_receipt")
    if any(not isinstance(evidence.get(key),str) or not evidence[key].strip()
           for key in required):
        return {**base,"blocks":["INCOMPLETE_EXTERNAL_DNS_EVIDENCE"]}
    # Intentionally do not infer authenticity from strings or self-attestation.
    return {**base,"status":"EXTERNAL_DNS_EVIDENCE_PRESENT_UNVERIFIED",
            "blocks":["RESOLVER_SIGNATURE_NOT_CRYPTOGRAPHICALLY_VERIFIED",
                      "SIGNED_DNS_RESPONSE_NOT_VERIFIED",
                      "EVIDENCE_BINDING_TO_HOST_AND_TIME_NOT_VERIFIED"],
            "record_sha256":provenance["record_sha256"],
            "scope":"offline evidence inventory only; no DNSSEC or signature verification"}
