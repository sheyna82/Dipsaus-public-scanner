"""Offline combined destination and resolved-IP review for EU research.

All resolved addresses must pass before a future connection. This does not
resolve DNS, connect sockets, verify TLS or authorize any network activity.
"""
from research.spoor2_eu_fetch_preflight_20261111 import review_eu_fetch_request
from research.spoor2_eu_resolved_ip_policy_20261111 import review_resolved_addresses

def review_eu_connection_plan(url, *, allowed_hosts, resolved_addresses):
    base={"status":"BLOCKED","connection_authorized":False,
          "trade_ready":False,"order_placement_enabled":False}
    destination=review_eu_fetch_request(url,allowed_hosts=allowed_hosts)
    if destination["status"]!="OFFLINE_PREFLIGHT_ONLY":
        return {**base,"blocks":destination["blocks"],
                "destination_review":destination}
    addresses=review_resolved_addresses(resolved_addresses)
    if addresses["status"]!="OFFLINE_PUBLIC_IP_REVIEW_ONLY":
        return {**base,"blocks":addresses["blocks"],
                "destination_review":destination,"address_review":addresses}
    return {**base,"status":"OFFLINE_CONNECTION_PLAN_ONLY",
            "blocks":["DNS_ORIGIN_NOT_ATTESTED","PINNED_TLS_CONNECTION_NOT_VERIFIED"],
            "destination_review":destination,"address_review":addresses,
            "host":destination["host"],"method":"GET",
            "redirects_allowed":False,
            "scope":"no DNS resolution or connection performed"}
