"""Research-only SEC EDGAR header parsing: acceptance is not public availability.

SEC states that EDGAR acceptance and website dissemination can differ. This
module parses externally supplied bytes; it does NOT retrieve or authenticate
SEC documents or prove a historical point-in-time publication.
"""
import hashlib
import re
from datetime import datetime
from zoneinfo import ZoneInfo
from urllib.parse import urlsplit

_HEADER = re.compile(rb"<ACCEPTANCE-DATETIME>\s*(\d{14})(?!\d)", re.I)


def inspect_sec_acceptance_header(raw_bytes, source_url, entry_at):
    if type(raw_bytes) is not bytes or not raw_bytes:
        raise ValueError("INVALID_SEC_HEADER_BYTES")
    if not isinstance(source_url, str):
        raise ValueError("INVALID_SEC_ARCHIVE_URL")
    parsed = urlsplit(source_url)
    if (parsed.scheme != "https" or parsed.hostname != "www.sec.gov"
            or not parsed.path.startswith("/Archives/edgar/data/")
            or parsed.username or parsed.password or parsed.query or parsed.fragment):
        raise ValueError("INVALID_SEC_ARCHIVE_URL")
    # A private submission can become public months after EDGAR acceptance.
    # Acceptance must never be used as a public-availability proxy for it.
    if re.search(rb"<PRIVATE-TO-PUBLIC(?:\s|>)", raw_bytes, re.I):
        raise ValueError("SEC_PRIVATE_TO_PUBLIC_ACCEPTANCE_UNUSABLE")
    matches = _HEADER.findall(raw_bytes)
    if len(matches) != 1:
        raise ValueError("MISSING_OR_AMBIGUOUS_SEC_ACCEPTANCE_TIME")
    try:
        accepted = datetime.strptime(matches[0].decode("ascii"), "%Y%m%d%H%M%S")
        eastern = ZoneInfo("America/New_York")
        accepted = accepted.replace(tzinfo=eastern)
        # Reject impossible local times and the repeated DST hour. Otherwise
        # naive replace(tzinfo=...) silently assigns a potentially wrong instant.
        wall = accepted.replace(tzinfo=None)
        if (accepted.astimezone(ZoneInfo("UTC")).astimezone(eastern).replace(tzinfo=None) != wall
                or wall.replace(tzinfo=eastern, fold=0).utcoffset()
                != wall.replace(tzinfo=eastern, fold=1).utcoffset()):
            raise ValueError("AMBIGUOUS_OR_NONEXISTENT_SEC_ACCEPTANCE_TIME")
        from integrated_historical_priority_provenance import _timestamp
        entry = _timestamp(entry_at)
    except (ValueError, UnicodeError) as exc:
        raise ValueError("INVALID_SEC_ACCEPTANCE_TIME") from exc
    if accepted >= entry:
        raise ValueError("SEC_ACCEPTANCE_NOT_BEFORE_ENTRY")
    return {
        "status": "RESEARCH_ONLY_SEC_HEADER_PARSED",
        "acceptance_at_et": accepted.isoformat(),
        "supplied_document_sha256": hashlib.sha256(raw_bytes).hexdigest(),
        "acceptance_precedes_entry": True,
        "source_url_claimed": source_url,
        "source_bytes_authenticity_independently_proven": False,
        "public_dissemination_time_independently_proven": False,
        "trade_ready": False,
        "eligible_for_performance_claim": False,
        "limitations": [
            "SEC acceptance time does not establish exact public dissemination time",
            "input bytes and source URL remain supplied claims, not independently fetched evidence",
        ],
    }
