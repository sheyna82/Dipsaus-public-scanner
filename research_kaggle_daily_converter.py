"""Strict offline conversion of Kaggle Huge Stock Market Dataset daily CSV.

Produces canonical OHLCV bytes for existing structural audit; does not verify
upstream rights, adjustment policies, or point-in-time availability.
"""
import csv
import io
import math
from research_daily_price_csv_audit import audit_daily_price_csv

SOURCE_COLUMNS = ("Date", "Open", "High", "Low", "Close", "Volume", "OpenInt")
TARGET_COLUMNS = ("date", "open", "high", "low", "close", "volume")


def convert_kaggle_daily_csv(payload):
    if not isinstance(payload, bytes) or not payload:
        raise ValueError("invalid_payload")
    try:
        content = payload.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ValueError("invalid_utf8") from exc
    reader = csv.DictReader(io.StringIO(content, newline=""))
    if reader.fieldnames is None or tuple(reader.fieldnames) != SOURCE_COLUMNS:
        raise ValueError("invalid_kaggle_columns")
    output = io.StringIO(newline="")
    writer = csv.writer(output, lineterminator="\n")
    writer.writerow(TARGET_COLUMNS)
    for row in reader:
        if None in row or any(row.get(column) is None for column in SOURCE_COLUMNS):
            raise ValueError("malformed_kaggle_row")
        if any(not row[column].strip() for column in SOURCE_COLUMNS):
            raise ValueError("blank_kaggle_value")
        # OpenInt is discarded only after verifying the field is numeric.
        try:
            open_interest = float(row["OpenInt"])
        except (ValueError, TypeError) as exc:
            raise ValueError("invalid_open_interest") from exc
        if not math.isfinite(open_interest) or open_interest < 0:
            raise ValueError("invalid_open_interest")
        writer.writerow([row[column] for column in SOURCE_COLUMNS[:-1]])
    converted = output.getvalue().encode("utf-8")
    audit_daily_price_csv(converted)
    return converted
