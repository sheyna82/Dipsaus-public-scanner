"""Independent SHA-256 check for supplied historical source bytes, research only."""
import hashlib
from integrated_historical_priority_provenance import validate

def verify_sources(registrations, source_bytes_by_hash):
    if not isinstance(source_bytes_by_hash, dict):
        raise ValueError("INVALID_SOURCE_MAP")
    evidence = validate(registrations)
    verified = []
    for record in registrations:
        digest = record["source_sha256"]
        raw = source_bytes_by_hash.get(digest)
        if type(raw) is not bytes:
            raise ValueError("SOURCE_BYTES_MISSING:" + str(record["id"]))
        actual = hashlib.sha256(raw).hexdigest()
        if actual != digest:
            raise ValueError("SOURCE_HASH_MISMATCH:" + str(record["id"]))
        verified.append({"id": record["id"], "source_sha256": digest,
                         "bytes_hash_verified": True, "trade_ready": False})
    return {"status": "RESEARCH_ONLY_SOURCE_BYTES_VERIFIED",
            "trade_ready": False, "source_bytes_verified": verified,
            "external_publication_time_independently_proven": False,
            "registrations": evidence["verified_registrations"],
            "limitations": ["hash match proves bytes match claimed digest, not publication date",
                            "source authenticity requires independent provenance beyond bytes"]}
