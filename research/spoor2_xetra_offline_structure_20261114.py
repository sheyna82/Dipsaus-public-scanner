"""Non-attesting offline inspection of bounded Xetra research bytes.

This is a structural sanity check, not exchange authority, instrument
identity, broker routing, or trade permission. Never extracts ZIP members.
"""
import csv
import io
import zipfile

MAX_UNCOMPRESSED = 100_000_000
MAX_MEMBERS = 1000


def inspect_xetra_bytes(kind, data):
    result = {
        "status": "BLOCKED", "kind": kind, "format_plausible": False,
        "source_attested": False, "instrument_segment_verified": False,
        "broker_route_verified": False, "trade_ready": False,
        "order_placement_enabled": False, "blocks": [],
    }
    if kind not in ("csv", "zip") or not isinstance(data, bytes) or not data:
        result["blocks"].append("INVALID_ARTIFACT_INPUT")
        return result
    try:
        if kind == "csv":
            # Structural only: never infer an authoritative schema from the header.
            text = data.decode("utf-8-sig")
            if "\x00" in text:
                result["blocks"].append("CSV_NUL_BYTE")
                return result
            reader = csv.reader(io.StringIO(text, newline=""), strict=True)
            header = next(reader)
            if len(header) < 2 or any(not cell.strip() for cell in header):
                result["blocks"].append("CSV_INVALID_HEADER")
                return result
            result["column_count"] = len(header)
        else:
            with zipfile.ZipFile(io.BytesIO(data)) as archive:
                infos = archive.infolist()
                if not infos or len(infos) > MAX_MEMBERS:
                    result["blocks"].append("ZIP_MEMBER_COUNT")
                    return result
                total = 0
                for info in infos:
                    name = info.filename
                    if (not name or name.startswith(("/", "\\")) or "\\" in name
                            or any(p in (".", "..") for p in name.split("/"))
                            or info.flag_bits & 1 or info.file_size < 0):
                        result["blocks"].append("ZIP_UNSAFE_MEMBER")
                        return result
                    total += info.file_size
                    if total > MAX_UNCOMPRESSED:
                        result["blocks"].append("ZIP_UNCOMPRESSED_SIZE_LIMIT")
                        return result
                # Test CRC and decompression without extraction. Enforce actual
                # per-member and aggregate bytes; metadata alone is untrusted.
                consumed = 0
                for info in infos:
                    with archive.open(info) as stream:
                        member_size = 0
                        while True:
                            chunk = stream.read(min(65536, MAX_UNCOMPRESSED + 1 - consumed))
                            if not chunk:
                                break
                            member_size += len(chunk)
                            consumed += len(chunk)
                            if consumed > MAX_UNCOMPRESSED or member_size > info.file_size:
                                result["blocks"].append("ZIP_UNCOMPRESSED_SIZE_LIMIT")
                                return result
                        if member_size != info.file_size:
                            result["blocks"].append("ZIP_MEMBER_LENGTH_MISMATCH")
                            return result
                result["member_count"] = len(infos)
    except (UnicodeError, csv.Error, StopIteration, zipfile.BadZipFile,
            RuntimeError, OSError, ValueError, NotImplementedError, EOFError):
        result["blocks"].append("ARTIFACT_FORMAT_ERROR")
        return result
    result["format_plausible"] = True
    result["blocks"].append("STRUCTURE_ONLY_NOT_INDEPENDENT_SOURCE_ATTESTATION")
    return result
