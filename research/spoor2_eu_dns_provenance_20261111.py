"""Offline DNS provenance audit: metadata never proves resolver authenticity."""
import hashlib
import ipaddress
import json
from research.spoor2_eu_connection_plan_20261111 import review_eu_connection_plan

def review_dns_provenance(url, *, allowed_hosts, resolved_addresses,
                          resolver_identity, observation_utc, claimed_dnssec=False,
                          claimed_independent=False):
    base={"status":"BLOCKED","dns_attested":False,"connection_authorized":False,
          "trade_ready":False,"order_placement_enabled":False}
    plan=review_eu_connection_plan(url,allowed_hosts=allowed_hosts,
                                   resolved_addresses=resolved_addresses)
    if plan["status"]!="OFFLINE_CONNECTION_PLAN_ONLY":
        return {**base,"blocks":["INVALID_CONNECTION_PLAN"]}
    if (not isinstance(resolver_identity,str) or not resolver_identity.strip()
        or resolver_identity.strip()!=resolver_identity or len(resolver_identity)>200
        or not isinstance(observation_utc,str) or len(observation_utc)>64
        or not observation_utc.endswith("Z")):
        return {**base,"blocks":["INVALID_DNS_PROVENANCE_METADATA"]}
    from datetime import datetime, timezone
    try:
        instant=datetime.fromisoformat(observation_utc.replace("Z","+00:00"))
        if instant.tzinfo is None or instant.utcoffset().total_seconds()!=0:
            raise ValueError("not UTC")
    except ValueError:
        return {**base,"blocks":["INVALID_DNS_PROVENANCE_METADATA"]}
    record={"host":plan["host"],
            "addresses":sorted(plan["address_review"]["validated_addresses"]),
            "resolver_identity_claim":resolver_identity,
            "observation_utc_claim":observation_utc}
    digest=hashlib.sha256(json.dumps(record,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    return {**base,"status":"OFFLINE_DNS_PROVENANCE_CLAIMS_ONLY",
            "blocks":["RESOLVER_IDENTITY_NOT_ATTESTED","DNS_RESPONSE_NOT_ATTESTED",
                      "DNSSEC_NOT_VERIFIED","INDEPENDENCE_NOT_VERIFIED"],
            "record":record,"record_sha256":digest,
            "scope":"untrusted caller claims; digest only checks local record integrity"}
