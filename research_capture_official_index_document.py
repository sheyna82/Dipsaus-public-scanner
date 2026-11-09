"""Isolated official-source byte capture; never grants index identity approval.

Use only in explicitly authorized research jobs. No live scanner dependency.
"""
import base64
import hashlib
from datetime import datetime, timezone
from urllib.parse import urlsplit
from urllib.request import build_opener, HTTPHandler, HTTPSHandler, Request
from urllib.error import HTTPError, URLError

ALLOWED_HOSTS=frozenset(("indexes.nasdaqomx.com","www.nasdaq.com"))
MAX_BYTES=2_000_000

class NoRedirect(HTTPHandler):
    pass

from urllib.request import HTTPRedirectHandler
class RejectRedirect(HTTPRedirectHandler):
    def redirect_request(self,req,fp,code,msg,headers,newurl):
        raise ValueError("OFFICIAL_SOURCE_REDIRECT_BLOCKED")

def capture_official_document(url, opener=None, now=None):
    parts=urlsplit(url)
    if (parts.scheme!="https" or parts.hostname not in ALLOWED_HOSTS or
        parts.username is not None or parts.password is not None or
        parts.port not in (None,443) or parts.fragment):
        raise ValueError("OFFICIAL_SOURCE_URL_BLOCKED")
    opener=opener or build_opener(HTTPSHandler(),RejectRedirect())
    req=Request(url,headers={"User-Agent":"DIPSAUS-research-evidence/1.0","Accept":"application/pdf,application/octet-stream"})
    with opener.open(req,timeout=20) as response:
        final_url=response.geturl()
        if final_url!=url or response.getcode()!=200:
            raise ValueError("OFFICIAL_SOURCE_RESPONSE_BLOCKED")
        raw=response.read(MAX_BYTES+1)
    if not raw or len(raw)>MAX_BYTES:
        raise ValueError("OFFICIAL_SOURCE_SIZE_BLOCKED")
    if parts.path.lower().endswith(".pdf") and not raw.startswith(b"%PDF-"):
        raise ValueError("OFFICIAL_SOURCE_NOT_PDF")
    stamp=(now or datetime.now(timezone.utc)).astimezone(timezone.utc).isoformat()
    return {"official_source_url":url,"official_document_sha256":hashlib.sha256(raw).hexdigest(),
            "official_document_base64":base64.b64encode(raw).decode("ascii"),
            "retrieval_method":"direct_https_no_redirect","retrieved_utc":stamp,
            "research_only":True,"independently_audited":False,"trade_ready":False}
