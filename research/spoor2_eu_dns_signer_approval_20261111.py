"""Offline DNS signer approval policy; evidence inventory, never key enrollment.

A fingerprint is not a trust anchor. Approval requires independently reviewed
provenance, host scope, key rotation and revocation. This module never mutates
the immutable production-independent default-deny trust registry.
"""
import hashlib
import json

REQUIRED_REVIEW_FIELDS=("signer_key_sha256","source_uri","source_sha256",
                        "reviewer_1","reviewer_2","reviewed_at_utc",
                        "hostname_scope","rotation_policy","revocation_policy")

def review_dns_signer_approval_proposal(proposal):
    base={"status":"BLOCKED","approval_granted":False,"key_trusted":False,
          "dns_admitted":False,"connection_authorized":False,
          "trade_ready":False,"order_placement_enabled":False}
    if not isinstance(proposal,dict) or set(proposal)!=set(REQUIRED_REVIEW_FIELDS):
        return {**base,"blocks":["INCOMPLETE_SIGNER_APPROVAL_PROPOSAL"]}
    if any(not isinstance(proposal[k],str) or not proposal[k].strip()
           or proposal[k].strip()!=proposal[k] or len(proposal[k])>1024
           for k in REQUIRED_REVIEW_FIELDS):
        return {**base,"blocks":["INVALID_SIGNER_APPROVAL_FIELD"]}
    for k in ("signer_key_sha256","source_sha256"):
        if len(proposal[k])!=64 or any(c not in "0123456789abcdef" for c in proposal[k]):
            return {**base,"blocks":["INVALID_SIGNER_APPROVAL_FINGERPRINT"]}
    if proposal["reviewer_1"]==proposal["reviewer_2"]:
        return {**base,"blocks":["NON_INDEPENDENT_APPROVAL_REVIEWERS"]}
    from datetime import datetime
    try:
        when=proposal["reviewed_at_utc"]
        if not when.endswith("Z"):
            raise ValueError("UTC required")
        datetime.fromisoformat(when.replace("Z","+00:00"))
    except ValueError:
        return {**base,"blocks":["INVALID_APPROVAL_REVIEW_TIME"]}
    digest=hashlib.sha256(json.dumps(proposal,sort_keys=True,
                        separators=(",",":")).encode("utf-8")).hexdigest()
    return {**base,"status":"SIGNER_APPROVAL_PROPOSAL_ONLY",
            "blocks":["SOURCE_PROVENANCE_NOT_INDEPENDENTLY_VERIFIED",
                      "REVIEWER_IDENTITIES_NOT_ATTESTED",
                      "TRUST_ANCHOR_ENROLLMENT_NOT_AUTHORIZED"],
            "proposal_sha256":digest,
            "scope":"self-reported proposal, not an approval or trust enrollment"}
