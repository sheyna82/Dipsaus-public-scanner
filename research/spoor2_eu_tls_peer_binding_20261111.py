"""Offline peer-binding review for a future pinned TLS socket.

Caller-supplied peer details are not network attestations. This module cannot
authorize fetching or trading, even if all supplied values agree.
"""
import ipaddress
from research.spoor2_eu_tls_contract_20261111 import review_eu_tls_contract

def review_eu_tls_peer_binding(url, *, allowed_hosts, resolved_addresses,
                               selected_address, sni_hostname,
                               certificate_hostname, certificate_validation,
                               observed_peer_address, observed_peer_port,
                               tls_hostname_checked, tls_chain_checked,
                               redirects_allowed=False, dns_reresolution_allowed=False):
    base={"status":"BLOCKED","connection_authorized":False,
          "trade_ready":False,"order_placement_enabled":False}
    contract=review_eu_tls_contract(
        url,allowed_hosts=allowed_hosts,resolved_addresses=resolved_addresses,
        selected_address=selected_address,sni_hostname=sni_hostname,
        certificate_hostname=certificate_hostname,
        certificate_validation=certificate_validation,
        redirects_allowed=redirects_allowed,
        dns_reresolution_allowed=dns_reresolution_allowed)
    if contract["status"]!="OFFLINE_TLS_CONTRACT_ONLY":
        return {**base,"blocks":["INVALID_TLS_CONTRACT"]}
    if not isinstance(observed_peer_address,str) or observed_peer_address.strip()!=observed_peer_address:
        return {**base,"blocks":["INVALID_PEER_ADDRESS"]}
    try:
        peer=ipaddress.ip_address(observed_peer_address).compressed
    except ValueError:
        return {**base,"blocks":["INVALID_PEER_ADDRESS"]}
    if peer!=contract["contract"]["selected_address"]:
        return {**base,"blocks":["PEER_ADDRESS_NOT_PINNED"]}
    if type(observed_peer_port) is not int or observed_peer_port!=443:
        return {**base,"blocks":["UNEXPECTED_PEER_PORT"]}
    if tls_hostname_checked is not True or tls_chain_checked is not True:
        return {**base,"blocks":["TLS_VALIDATION_NOT_REPORTED"]}
    return {**base,"status":"OFFLINE_PEER_CLAIMS_MATCH_ONLY",
            "blocks":["SOCKET_OBSERVATION_NOT_INDEPENDENTLY_ATTESTED",
                      "TLS_HANDSHAKE_NOT_INDEPENDENTLY_ATTESTED"],
            "contract_sha256":contract["contract_sha256"],
            "scope":"caller-supplied peer claims; no socket, DNS, TLS, or HTTP performed"}
