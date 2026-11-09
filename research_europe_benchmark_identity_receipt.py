"""Independent EU benchmark identity evidence contract. Offline, fail closed.

An evidence receipt documents review, not proof of external truth by itself.
"""
import hashlib
import base64
import binascii
import json
from urllib.parse import urlsplit
from datetime import date

REQUIRED=("symbol","provider_symbol","official_index_name","official_publisher",
          "official_source_url","official_document_sha256","official_document_base64","reviewer",
          "review_day","methodology","identity_match","currency_match",
          "price_vs_total_return_match","value_discrepancy_resolved")

def validate_receipt(receipt):
    if not isinstance(receipt,dict):raise ValueError("INVALID_RECEIPT")
    if any(k not in receipt for k in REQUIRED):raise ValueError("MISSING_EVIDENCE")
    for k in ("symbol","provider_symbol","official_index_name","official_publisher",
              "official_source_url","reviewer","methodology"):
        if not isinstance(receipt[k],str) or not receipt[k].strip():
            raise ValueError("INVALID_EVIDENCE")
    try:
        url=urlsplit(receipt["official_source_url"])
        valid_url=(url.scheme=="https" and bool(url.hostname) and
                   url.username is None and url.password is None and
                   url.port in (None,443) and not url.fragment and
                   url.hostname==url.hostname.lower())
    except ValueError:
        valid_url=False
    if not valid_url:
        raise ValueError("INVALID_OFFICIAL_SOURCE")
    if receipt["official_publisher"].strip().lower()=="nasdaq" and url.hostname not in ("indexes.nasdaqomx.com","www.nasdaq.com"):
        raise ValueError("OFFICIAL_PUBLISHER_HOST_MISMATCH")
    h=receipt["official_document_sha256"]
    if not isinstance(h,str) or len(h)!=64 or any(x not in "0123456789abcdef" for x in h):
        raise ValueError("INVALID_EVIDENCE_HASH")
    try:
        raw=base64.b64decode(receipt["official_document_base64"],validate=True)
    except (TypeError,ValueError,binascii.Error) as exc:
        raise ValueError("INVALID_OFFICIAL_DOCUMENT_BYTES") from exc
    if not raw or len(raw)>2000000 or hashlib.sha256(raw).hexdigest()!=h:
        raise ValueError("OFFICIAL_DOCUMENT_HASH_MISMATCH")
    if date.fromisoformat(receipt["review_day"]).isoformat()!=receipt["review_day"]:
        raise ValueError("INVALID_REVIEW_DAY")
    for k in ("identity_match","currency_match","price_vs_total_return_match",
              "value_discrepancy_resolved"):
        if receipt[k] is not True:raise ValueError("UNRESOLVED_BENCHMARK_EVIDENCE:"+k)
    normalized={k:receipt[k] for k in REQUIRED}
    digest=hashlib.sha256(json.dumps(normalized,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    return {"receipt_sha256":digest,"provider_symbol":receipt["provider_symbol"],
            "identity_evidence_complete":True,"research_only":True,
            "trade_ready":False,"independently_audited":False}
