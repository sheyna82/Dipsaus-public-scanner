"""Research-only matching of MIC candidates against parsed CSV rows.

Matching is documentary evidence, never proof of authority, current
registration, broker routing, or permission to trade.
"""
import csv
import io

CANDIDATES = ("XAMS", "XETR", "XHEL")


def inspect_mic_candidates(csv_bytes, *, mic_column="MIC"):
    result = {
        "status": "BLOCKED", "candidate_matches": {},
        "source_attested": False, "mic_registered": False,
        "degiro_fee_verified": False, "trade_ready": False,
        "order_placement_enabled": False, "blocks": [],
    }
    from research.spoor2_iso_mic_csv_intake_20261113 import inspect_iso_mic_csv
    intake = inspect_iso_mic_csv(csv_bytes)
    if not intake["csv_syntax_valid"]:
        result["blocks"].append("CSV_INTAKE_REJECTED")
        return result
    text = csv_bytes.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text, newline=""), strict=True)
    if mic_column not in (reader.fieldnames or ()):
        result["blocks"].append("MIC_COLUMN_NOT_FOUND")
        return result
    matches = {candidate: [] for candidate in CANDIDATES}
    for row in reader:
        value = row[mic_column]
        if value in matches:
            matches[value].append(dict(row))
    for candidate, rows in matches.items():
        result["candidate_matches"][candidate] = {
            "count": len(rows), "unique": len(rows) == 1,
        }
        if len(rows) != 1:
            result["blocks"].append("MISSING_OR_DUPLICATE_MIC_" + candidate)
    result["blocks"].extend((
        "OFFICIAL_CSV_ORIGIN_NOT_ATTESTED",
        "MIC_STATUS_AND_EFFECTIVE_DATE_NOT_VERIFIED",
        "INSTRUMENT_TO_VENUE_LINK_NOT_VERIFIED",
    ))
    return result
