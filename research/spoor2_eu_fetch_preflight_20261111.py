"""Strict preflight policy for a future isolated EU HTTPS source fetcher.

Pure offline validation only: no DNS, sockets, HTTP, secrets, or live scanner
integration. Host allowlisting alone cannot prevent DNS rebinding; a future
fetcher MUST validate resolved IPs, TLS, and every redirect at connection time.
"""
import ipaddress
from urllib.parse import urlsplit

def review_eu_fetch_request(url, *, allowed_hosts):
    base={"status":"BLOCKED","fetch_allowed":False,"trade_ready":False,
          "order_placement_enabled":False}
    if not isinstance(url,str) or not isinstance(allowed_hosts,(tuple,list,frozenset)):
        return {**base,"blocks":["INVALID_FETCH_POLICY_INPUT"]}
    if not allowed_hosts or any(not isinstance(h,str) or not h or h!=h.lower()
                                or h.startswith(".") or h.endswith(".")
                                or any(c not in "abcdefghijklmnopqrstuvwxyz0123456789-." for c in h)
                                for h in allowed_hosts):
        return {**base,"blocks":["INVALID_ALLOWLIST"]}
    if any(c.isspace() or ord(c)<32 or ord(c)==127 for c in url):
        return {**base,"blocks":["URL_CONTROL_OR_WHITESPACE"]}
    try:
        p=urlsplit(url)
        host=p.hostname
        if (p.scheme!="https" or not host or p.username is not None or
            p.password is not None or p.fragment or p.port not in (None,443)
            or p.netloc.endswith(".") or "\\" in url):
            return {**base,"blocks":["UNSAFE_URL"]}
        try:
            ipaddress.ip_address(host)
            return {**base,"blocks":["IP_LITERAL_NOT_ALLOWED"]}
        except ValueError:
            pass
        if host not in allowed_hosts:
            return {**base,"blocks":["HOST_NOT_ALLOWLISTED"]}
    except ValueError:
        return {**base,"blocks":["UNSAFE_URL"]}
    return {**base,"status":"OFFLINE_PREFLIGHT_ONLY",
            "blocks":["DNS_TLS_AND_RESPONSE_NOT_VERIFIED"],
            "host":host,
            "method":"GET",
            "redirects_allowed":False,
            "scope":"no network request executed"}
