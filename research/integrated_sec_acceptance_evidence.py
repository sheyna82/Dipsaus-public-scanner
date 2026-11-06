"""Research-only SEC EDGAR header parsing: acceptance is not public availability.

SEC states that EDGAR acceptance and website dissemination can differ. This
module parses externally supplied bytes; it does NOT retrieve or authenticate
SEC documents or prove a historical point-in-time publication.
"""
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
    matches = _HEADER.findall(raw_bytes)
    if len(matches) != 1:
        raise ValueError("MISSING_OR_AMBIGUOUS_SEC_ACCEPTANCE_TIME")
    try:
        accepted = datetime.strptime(matches[0].decode("ascii"), "%Y%m%d%H%M%S")
        accepted = accepted.replace(tzinfo=ZoneInfo("America/New_York"))
        from integrated_historical_priority_provenance import _timestamp
        entry = _timestamp(entry_at)
    except (ValueError, UnicodeError) as exc:
        raise ValueError("INVALID_SEC_ACCEPTANCE_TIME") from exc
    if accepted >= entry:
        raise ValueError("SEC_ACCEPTANCE_NOT_BEFORE_ENTRY")
    return {
        "status": "RESEARCH_ONLY_SEC_HEADER_PARSED",
        "acceptance_at_et": accepted.isoformat(),
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
