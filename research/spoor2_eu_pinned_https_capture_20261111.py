"""Pinned, read-only HTTPS capture. Never trades, redirects, or resolves DNS.

Not wired to production. Callers must supply independently vetted DNS answers;
the TCP socket connects directly to the selected public IP, with SNI and
certificate hostname validation against the original allowlisted hostname.
"""
import hashlib
import http.client
import socket
import ssl
from urllib.parse import urlsplit
from research.spoor2_eu_tls_contract_20261111 import review_eu_tls_contract

def capture_pinned_https(url, *, allowed_hosts, resolved_addresses,
                         selected_address, timeout_seconds=10,
                         max_response_bytes=1048576, transport=None):
    """Return fail-closed result; optional transport is only for offline tests.

    A transport override cannot attest a live capture, so its output is
    always classified as simulated and never externally authenticated.
    """
    base={"status":"BLOCKED","trade_ready":False,
          "order_placement_enabled":False,"connection_authorized":False}
    try:
        parsed=urlsplit(url) if isinstance(url,str) else None
        host=parsed.hostname if parsed else None
    except ValueError:
        return {**base,"blocks":["INVALID_URL"]}
    review=review_eu_tls_contract(
        url,allowed_hosts=allowed_hosts,resolved_addresses=resolved_addresses,
        selected_address=selected_address,sni_hostname=host,
        certificate_hostname=host,certificate_validation=True,
        timeout_seconds=timeout_seconds,max_response_bytes=max_response_bytes)
    if review["status"]!="OFFLINE_TLS_CONTRACT_ONLY":
        return {**base,"blocks":["INVALID_TLS_CONTRACT"]}
    contract=review["contract"]
    path=(parsed.path or "/")+("?" + parsed.query if parsed.query else "")
    # Host and path have already passed the destination preflight.
    if transport is not None:
        return {**base,"status":"SIMULATED_TRANSPORT_ONLY",
                "blocks":["TRANSPORT_INJECTED_NOT_ATTESTED"],
                "contract_sha256":review["contract_sha256"]}
    raw=None
    tls=None
    try:
        raw=socket.create_connection((contract["selected_address"],443),
                                     timeout=timeout_seconds)
        peer=raw.getpeername()
        if peer[0]!=contract["selected_address"] or peer[1]!=443:
            return {**base,"blocks":["SOCKET_PEER_MISMATCH"]}
        context=ssl.create_default_context()
        context.check_hostname=True
        context.verify_mode=ssl.CERT_REQUIRED
        tls=context.wrap_socket(raw,server_hostname=host)
        raw=None
        tls.settimeout(timeout_seconds)
        tls_peer=tls.getpeername()
        if tls_peer[0]!=contract["selected_address"] or tls_peer[1]!=443:
            return {**base,"blocks":["TLS_SOCKET_PEER_MISMATCH"]}
        request=("GET "+path+" HTTP/1.1\\r\\nHost: "+host+
                 "\\r\\nAccept: application/octet-stream\\r\\n"+
                 "Accept-Encoding: identity\\r\\nConnection: close\\r\\n\\r\\n")
        tls.sendall(request.encode("ascii"))
        response=http.client.HTTPResponse(tls)
        response.begin()
        if response.status!=200:
            return {**base,"blocks":["UNEXPECTED_HTTP_STATUS"],"http_status":response.status}
        if response.getheader("Content-Encoding","identity").lower()!="identity":
            return {**base,"blocks":["UNSUPPORTED_CONTENT_ENCODING"]}
        body=response.read(max_response_bytes+1)
        if len(body)>max_response_bytes:
            return {**base,"blocks":["RESPONSE_SIZE_EXCEEDED"]}
        return {**base,"status":"HTTPS_CAPTURED_READ_ONLY",
                "blocks":["EXTERNAL_SOURCE_INDEPENDENCE_NOT_VERIFIED",
                          "TRADING_ADMISSION_NOT_GRANTED"],
                "http_status":200,"body_sha256":hashlib.sha256(body).hexdigest(),
                "body_size":len(body),"selected_address":contract["selected_address"],
                "host":host,"contract_sha256":review["contract_sha256"]}
    except (OSError,ssl.SSLError,http.client.HTTPException,UnicodeError,ValueError):
        return {**base,"blocks":["HTTPS_CAPTURE_FAILED"]}
    finally:
        if tls is not None: tls.close()
        if raw is not None: raw.close()
