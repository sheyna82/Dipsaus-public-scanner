"""Offline EU source-separation audit, not an external attestation.

Rejects obvious same-provider/same-family evidence reuse across broker ask
and technical levels. Self-declared provenance can never prove independence.
"""
from urllib.parse import urlsplit

ROLES = ("ask", "target_bid", "invalidation", "fx", "fees")
TECHNICAL = ("target_bid", "invalidation")

def audit_eu_source_separation(candidate):
    result = {"status": "BLOCKED", "trade_ready": False,
              "order_placement_enabled": False}
    if not isinstance(candidate, dict):
        return {**result, "blocks": ["INVALID_CANDIDATE"]}
    identities = {}
    canonical_urls = {}
    blocks = []
    for role in ROLES:
        record = candidate.get(role + "_evidence")
        if not isinstance(record, dict):
            blocks.append(role.upper() + "_SOURCE_MISSING")
            continue
        fields = ("provider_id", "source_family", "source_record_id", "source_url")
        if any(not isinstance(record.get(k), str) or not record[k].strip() for k in fields):
            blocks.append(role.upper() + "_SOURCE_IDENTITY_INCOMPLETE")
            continue
        provider, family, source_id, url = (record[k].strip() for k in fields)
        try:
            parsed = urlsplit(url)
            valid = (parsed.scheme == "https" and parsed.hostname is not None
                     and not parsed.username and not parsed.password
                     and not any(ch.isspace() for ch in url)
                     and "\\" not in url
                     and parsed.hostname != ""
                     and not any(not label for label in parsed.hostname.rstrip(".").split("."))
                     and parsed.hostname.endswith("..") is False
                     and parsed.port in (None, 443)
                     and parsed.fragment == "")
        except ValueError:
            valid = False
        if not valid:
            blocks.append(role.upper() + "_SOURCE_URL_INVALID")
            continue
        identities[role] = (provider.casefold(), family.casefold(),
                            source_id, parsed.hostname.casefold())
        # Compare only unambiguous equivalences: DNS host case, default HTTPS
        # port and an empty path versus /. Preserve query and path spelling.
        canonical_urls[role] = (parsed.hostname.casefold().rstrip("."),
                                parsed.path or "/", parsed.query)
    if "ask" in identities:
        for role in TECHNICAL:
            if role not in identities:
                continue
            ask, other = identities["ask"], identities[role]
            if ask[0] == other[0] or ask[1] == other[1]:
                blocks.append("BROKER_TECHNICAL_SOURCE_NOT_SEPARATED")
            if ask[0] == other[0] and ask[2] == other[2]:
                blocks.append("SOURCE_RECORD_REUSED")
            if canonical_urls["ask"] == canonical_urls[role]:
                blocks.append("BROKER_TECHNICAL_SOURCE_URL_REUSED")
    blocks.append("EXTERNAL_SOURCE_ATTESTATION_NOT_CONNECTED")
    return {**result, "blocks": list(dict.fromkeys(blocks)),
            "source_separation_metadata_complete": len(identities) == len(ROLES),
            "status": "PROVENANCE_ONLY_NOT_ATTESTED" if len(blocks) == 1 else "BLOCKED"}
