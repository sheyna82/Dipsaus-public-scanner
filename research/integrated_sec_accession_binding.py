"""Strict SEC accession binding for supplied EDGAR archive documents.

This checks internal consistency only. Neither the URL nor the bytes are
independently authenticated and no historical public availability is proven.
"""
import re
from urllib.parse import urlsplit

_ACCESSION = re.compile(
    rb"(?m)^(?:<ACCESSION-NUMBER>\s*|ACCESSION NUMBER:\s*)(\d{10}-\d{2}-\d{6})\s*$",
    re.I,
)


def verify_sec_accession_binding(raw_bytes, source_url):
    if type(raw_bytes) is not bytes or not raw_bytes:
        raise ValueError("INVALID_SEC_DOCUMENT_BYTES")
    if not isinstance(source_url, str):
        raise ValueError("INVALID_SEC_ARCHIVE_URL")
    parsed = urlsplit(source_url)
    if (parsed.scheme != "https" or parsed.netloc != "www.sec.gov"
            or parsed.query or parsed.fragment):
        raise ValueError("INVALID_SEC_ARCHIVE_URL")
    path = parsed.path
    match = re.fullmatch(
        r"/Archives/edgar/data/([1-9]\d*)/(\d{18})/([0-9]{10}-[0-9]{2}-[0-9]{6})\.txt",
        path, re.I)
    if match is None:
        raise ValueError("UNSUPPORTED_SEC_COMPLETE_SUBMISSION_URL")
    matches = _ACCESSION.findall(raw_bytes)
    if len(matches) != 1:
        raise ValueError("MISSING_OR_AMBIGUOUS_SEC_ACCESSION")
    accession = matches[0].decode("ascii")
    if accession != match.group(3) or accession.replace("-", "") != match.group(2):
        raise ValueError("SEC_ACCESSION_URL_MISMATCH")
    return {
        "status": "RESEARCH_ONLY_SEC_ACCESSION_CONSISTENT",
        "accession": accession,
        "internal_accession_consistency": True,
        "source_bytes_authenticity_independently_proven": False,
        "public_dissemination_time_independently_proven": False,
        "trade_ready": False,
    }
