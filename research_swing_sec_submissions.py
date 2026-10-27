"""Offline SEC submissions normalization: filings are NOT earnings surprises.

No HTTP requests, secrets, trading actions or inferred first-observation times.
The SEC filing acceptance timestamp is not necessarily the public release time.
"""
from datetime import datetime, timezone


def sec_submissions_endpoint(cik):
    """Build official read-only endpoint; do not fetch automatically."""
    if type(cik) is not int or not 1 <= cik <= 9999999999:
        raise ValueError("invalid_cik")
    return f"https://data.sec.gov/submissions/CIK{cik:010d}.json"


def normalize_sec_recent_filings(payload, *, forms=("8-K", "10-Q", "10-K")):
    """Extract filing metadata from parallel SEC recent arrays, fail closed.

    Returns filing candidates only. No verified event timestamp, historical
    source-observation timestamp, earnings classification or return label.
    """
    if not isinstance(payload, dict):
        raise ValueError("invalid_payload")
    cik = payload.get("cik")
    if type(cik) is not int or not 1 <= cik <= 9999999999:
        raise ValueError("invalid_cik")
    recent = payload.get("filings", {}).get("recent")
    if not isinstance(recent, dict):
        raise ValueError("missing_recent_filings")
    fields = ("accessionNumber", "form", "filingDate", "acceptanceDateTime", "primaryDocument")
    arrays = [recent.get(field) for field in fields]
    if any(not isinstance(items, list) for items in arrays):
        raise ValueError("missing_filing_columns")
    if len(set(map(len, arrays))) != 1:
        raise ValueError("misaligned_filing_columns")
    results = []
    seen = set()
    for accession, form, filing_date, accepted, document in zip(*arrays):
        if form not in forms:
            continue
        if (not isinstance(accession, str) or
                not isinstance(document, str) or not document or "/" in document or
                not isinstance(filing_date, str) or
                not isinstance(accepted, str)):
            raise ValueError("invalid_filing_metadata")
        try:
            datetime.strptime(filing_date, "%Y-%m-%d")
            parsed = datetime.fromisoformat(accepted.replace("Z", "+00:00"))
        except ValueError as exc:
            raise ValueError("invalid_filing_timestamp") from exc
        if parsed.tzinfo is None or parsed.utcoffset() is None:
            raise ValueError("unverified_acceptance_timezone")
        if accession in seen:
            raise ValueError("duplicate_accession")
        seen.add(accession)
        accession_compact = accession.replace("-", "")
        if not accession_compact.isdigit() or len(accession_compact) != 18:
            raise ValueError("invalid_accession")
        results.append({
            "cik": cik, "accession": accession, "form": form,
            "filing_date": filing_date,
            "acceptance_at_utc": parsed.astimezone(timezone.utc).isoformat(),
            "filing_url": f"https://www.sec.gov/Archives/edgar/data/{cik}/{accession_compact}/{document}",
            "release_timestamp_verified": False,
            "first_observed_at": None,
            "research_eligible": False,
            "trade_ready": False,
        })
    return results
