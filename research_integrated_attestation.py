"""Offline integrated historical attestation rehearsal, research only.

Chain structure, key-policy metadata and Ed25519 signatures are checked.
No independent timestamp, trust anchor or complete-universe attestation.
"""
from research_attestation_chain import check_attestation_chain
from research_ed25519_verifier import verify_ed25519_batch
from research_key_rotation_policy import assess_key_rotation

BLOCKED = {"trade_ready": False, "order_placement_enabled": False,
           "source_authenticity_independently_verified": False,
           "archive_integrity_independently_verified": False,
           "independently_attested": False}

def verify_historical_attestations(records, *, keys, expected_fingerprints):
    base = {**BLOCKED, "status": "INTEGRATED_ATTESTATION_BLOCKED"}
    if (not isinstance(records, list) or not isinstance(expected_fingerprints, dict)
            or not isinstance(keys, list)):
        return {**base, "reason": "INVALID_INPUT"}
    chain_records = []
    for item in records:
        if not isinstance(item, dict) or set(item) != {
                "sequence", "batch_digest", "previous_digest", "closed_utc",
                "attested_utc", "key_id", "signature", "public_key_pem"}:
            return {**base, "reason": "INVALID_ATTESTATION_RECORD"}
        chain_records.append({
            "sequence": item["sequence"], "batch_digest": item["batch_digest"],
            "previous_digest": item["previous_digest"],
            "closed_utc": item["closed_utc"], "attested_utc": item["attested_utc"],
            "key_id": item["key_id"], "signature_verified_externally": False})
    chain = check_attestation_chain(chain_records)
    if chain["status"] != "ATTESTATION_CHAIN_STRUCTURALLY_CONSISTENT":
        return {**base, "reason": "CHAIN_BLOCKED",
                "detail": chain.get("reason")}
    for item in records:
        key_id = item["key_id"]
        fingerprint = expected_fingerprints.get(key_id)
        policy = assess_key_rotation(
            keys, key_id=key_id, attested_utc=item["attested_utc"],
            expected_public_key_sha256=fingerprint)
        if policy["status"] != "KEY_POLICY_STRUCTURALLY_ACCEPTED":
            return {**base, "reason": "KEY_POLICY_BLOCKED",
                    "detail": policy.get("reason")}
        selected = [k for k in keys if k["key_id"] == key_id]
        if len(selected) != 1 or selected[0]["public_key_pem"] != item["public_key_pem"]:
            return {**base, "reason": "KEY_MATERIAL_MISMATCH"}
        signature = verify_ed25519_batch(
            item["batch_digest"], item["signature"], item["public_key_pem"])
        if signature["status"] != "ED25519_SIGNATURE_VALID":
            return {**base, "reason": "SIGNATURE_BLOCKED",
                    "detail": signature.get("reason", signature["status"])}
    return {**BLOCKED, "status": "INTEGRATED_ATTESTATION_RESEARCH_ONLY",
            "verified_cryptographic_signatures": len(records),
            "independently_attested": False,
            "note": "Supplied key registry, fingerprints and times are not trusted anchors."}
