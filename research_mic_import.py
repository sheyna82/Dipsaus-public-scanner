"""Fail-closed offline handoff from source snapshot to MIC CSV parser.

The snapshot gate checks caller-supplied URL and digest claims; it does not
authenticate the publisher. Never promote metadata consistency into trust.
"""
from research_official_source_snapshot import assess_official_snapshot
from research_iso_mic_parser import parse_mic_csv

BLOCKED = {"trade_ready": False, "order_placement_enabled": False,
           "source_authenticity_independently_verified": False}


def validate_mic_snapshot(*, body, source_url, approved_url, response_status,
                          expected_sha256, columns, publication_date,
                          effective_date, as_of, redirect_location=None):
    snapshot = assess_official_snapshot(
        body=body, source_url=source_url, approved_url=approved_url,
        response_status=response_status, redirect_location=redirect_location,
        expected_sha256=expected_sha256)
    if snapshot.get("status") != "OFFLINE_SNAPSHOT_METADATA_CONSISTENT":
        return {**BLOCKED, "status": "MIC_IMPORT_BLOCKED",
                "reason": "SNAPSHOT_REJECTED",
                "source_reason": snapshot.get("reason")}
    try:
        csv_text = body.decode("utf-8-sig")
    except (UnicodeError, AttributeError):
        return {**BLOCKED, "status": "MIC_IMPORT_BLOCKED", "reason": "INVALID_ENCODING"}
    # The digest is bound to the original raw bytes, including any UTF-8 BOM.
    # The parser separately checks the exact decoded text digest, avoiding
    # accidental conflation of text normalization with source integrity.
    import hashlib
    parser_digest = hashlib.sha256(csv_text.encode("utf-8")).hexdigest()
    parsed = parse_mic_csv(
        csv_text, columns=columns, publication_date=publication_date,
        effective_date=effective_date, as_of=as_of,
        expected_sha256=parser_digest)
    if parsed.get("status") != "OFFLINE_MIC_SCHEMA_VALIDATED":
        return {**BLOCKED, "status": "MIC_IMPORT_BLOCKED",
                "reason": "PARSER_REJECTED", "parser_reason": parsed.get("reason")}
    return {**BLOCKED, "status": "OFFLINE_MIC_IMPORT_CONSISTENT",
            "source_sha256": snapshot["sha256"],
            "records": parsed["records"],
            "publication_date": parsed["publication_date"],
            "effective_date": parsed["effective_date"],
            "warning": "Metadata and CSV schema only; publisher not authenticated."}
