"""Offline TLS socket-binding requirements; never authorizes network access."""
import hashlib
import ipaddress
import json
from research.spoor2_eu_connection_plan_20261111 import review_eu_connection_plan

def review_eu_tls_contract(url, *, allowed_hosts, resolved_addresses, selected_address,
                           sni_hostname, certificate_hostname, certificate_validation,
                           redirects_allowed=False, dns_reresolution_allowed=False,
                           timeout_seconds=10, max_response_bytes=1048576,
                           claimed_tls_verified=False, plan_digest=None):
    base = {"status":"BLOCKED", "connection_authorized":False,
            "trade_ready":False, "order_placement_enabled":False}
    plan = review_eu_connection_plan(url, allowed_hosts=allowed_hosts,
                                      resolved_addresses=resolved_addresses)
    if plan["status"] != "OFFLINE_CONNECTION_PLAN_ONLY":
        return {**base, "blocks":["INVALID_CONNECTION_PLAN"], "connection_review":plan}
    host = plan["host"]
    valid = plan["address_review"]["validated_addresses"]
    try:
        address = ipaddress.ip_address(selected_address).compressed
    except (ValueError, TypeError):
        return {**base, "blocks":["INVALID_SELECTED_ADDRESS"]}
    if address not in valid:
        return {**base, "blocks":["ADDRESS_NOT_IN_VALIDATED_SET"]}
    if sni_hostname != host or certificate_hostname != host:
        return {**base, "blocks":["TLS_HOSTNAME_MISMATCH"]}
    if certificate_validation is not True:
        return {**base, "blocks":["CERTIFICATE_VALIDATION_REQUIRED"]}
    if redirects_allowed is not False or dns_reresolution_allowed is not False:
        return {**base, "blocks":["UNSAFE_CONNECTION_BEHAVIOR"]}
    if (isinstance(timeout_seconds,bool) or not isinstance(timeout_seconds,int)
        or not 1 <= timeout_seconds <= 30 or isinstance(max_response_bytes,bool)
        or not isinstance(max_response_bytes,int) or not 1 <= max_response_bytes <= 10485760):
        return {**base, "blocks":["INVALID_RESOURCE_LIMITS"]}
    contract = {"url":url, "host":host, "selected_address":address,
                "validated_addresses":valid, "sni_hostname":host,
                "certificate_hostname":host, "certificate_validation_required":True,
                "redirects_allowed":False, "dns_reresolution_allowed":False,
                "timeout_seconds":timeout_seconds, "max_response_bytes":max_response_bytes}
    digest = hashlib.sha256(json.dumps(contract,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    if plan_digest is not None and plan_digest != digest:
        return {**base, "blocks":["CONTRACT_DIGEST_MISMATCH"]}
    return {**base, "status":"OFFLINE_TLS_CONTRACT_ONLY",
            "blocks":["TLS_HANDSHAKE_NOT_ATTESTED","SOCKET_PEER_NOT_ATTESTED"],
            "contract":contract, "contract_sha256":digest,
            "scope":"offline requirements only; no DNS, socket, TLS or HTTP executed"}
