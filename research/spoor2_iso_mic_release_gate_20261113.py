"""Offline ISO 10383 publication/effective-date gate; never attests a MIC.

A publication containing future-effective changes cannot be used as proof
that those changes are already active. No network access or trading authority.
"""
from datetime import date


def audit_iso_mic_release(*, publication_date, implementation_date,
                          as_of_date, dataset_sha256=None,
                          parsed_mic_records=None):
    out = {
        "status": "BLOCKED", "source_attested": False,
        "mic_registered": False, "trade_ready": False,
        "order_placement_enabled": False, "blocks": [],
    }
    dates = []
    for raw in (publication_date, implementation_date, as_of_date):
        if not isinstance(raw, str):
            out["blocks"].append("INVALID_RELEASE_DATE")
            return out
        try:
            parsed = date.fromisoformat(raw)
            if parsed.isoformat() != raw:
                raise ValueError("Noncanonical date")
            dates.append(parsed)
        except ValueError:
            out["blocks"].append("INVALID_RELEASE_DATE")
            return out
    published, effective, as_of = dates
    if effective < published:
        out["blocks"].append("IMPLEMENTATION_BEFORE_PUBLICATION")
    if as_of < published:
        out["blocks"].append("RELEASE_NOT_YET_PUBLISHED")
    if as_of < effective:
        out["blocks"].append("RELEASE_CHANGES_NOT_YET_EFFECTIVE")
    if not isinstance(dataset_sha256, str) or len(dataset_sha256) != 64 or any(
            c not in "0123456789abcdef" for c in dataset_sha256):
        out["blocks"].append("OFFICIAL_DATASET_DIGEST_MISSING")
    # A caller-supplied digest or parsed rows cannot prove source provenance.
    if parsed_mic_records is not None and not isinstance(parsed_mic_records, list):
        out["blocks"].append("INVALID_PARSED_MIC_RECORDS")
    out["blocks"].extend((
        "OFFICIAL_DATASET_ORIGIN_NOT_ATTESTED",
        "INDIVIDUAL_MIC_REGISTRATION_NOT_ATTESTED",
    ))
    return out
