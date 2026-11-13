"""Bounded offline Xetra static reference ZIP inspection, not source attestation."""
import hashlib
import io
import zipfile

MAX_ARCHIVE_BYTES = 30_000_000
MAX_TOTAL_UNCOMPRESSED = 150_000_000
MAX_MEMBER_UNCOMPRESSED = 50_000_000
MAX_MEMBERS = 1000


def inspect_xetra_static_zip(data):
    out = dict(status="BLOCKED", sha256=None, zip_container_valid=False,
               member_count=0, source_attested=False,
               instrument_segment_verified=False, broker_route_verified=False,
               trade_ready=False, order_placement_enabled=False, blocks=[])
    if not isinstance(data, bytes) or not data or len(data) > MAX_ARCHIVE_BYTES:
        out["blocks"].append("INVALID_OR_OVERSIZED_XETRA_ZIP")
        return out
    out["sha256"] = hashlib.sha256(data).hexdigest()
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            members = archive.infolist()
            names = [item.filename for item in members]
            if not members or len(members) > MAX_MEMBERS or len(names) != len(set(names)):
                out["blocks"].append("DUPLICATE_OR_EXCESSIVE_XETRA_ZIP_MEMBERS")
                return out
            if any(name.startswith("/") or "\\" in name or ".." in name.split("/")
                   or not name for name in names):
                out["blocks"].append("UNSAFE_XETRA_ZIP_MEMBER_PATH")
                return out
            if any((item.flag_bits & 0x1) or item.file_size > MAX_MEMBER_UNCOMPRESSED
                   or item.file_size < 0 or item.compress_size < 0
                   for item in members):
                out["blocks"].append("UNSUPPORTED_OR_OVERSIZED_XETRA_ZIP_MEMBER")
                return out
            if sum(item.file_size for item in members) > MAX_TOTAL_UNCOMPRESSED:
                out["blocks"].append("EXCESSIVE_XETRA_ZIP_UNCOMPRESSED_SIZE")
                return out
            # CRC and decompression checked, bounded by declared per-member sizes.
            for item in members:
                if item.is_dir():
                    continue
                with archive.open(item) as stream:
                    total = 0
                    while True:
                        chunk = stream.read(65536)
                        if not chunk:
                            break
                        total += len(chunk)
                        if total > MAX_MEMBER_UNCOMPRESSED or total > item.file_size:
                            out["blocks"].append("XETRA_ZIP_MEMBER_SIZE_MISMATCH")
                            return out
            out["member_count"] = len(members)
            out["zip_container_valid"] = True
    except (zipfile.BadZipFile, OSError, ValueError, RuntimeError,
            NotImplementedError, EOFError):
        out["blocks"].append("INVALID_XETRA_ZIP_CONTAINER")
        return out
    out["blocks"].extend(("ORIGINAL_XETRA_SOURCE_NOT_ATTESTED",
                          "INSTRUMENT_SEGMENT_NOT_VERIFIED",
                          "DEGIRO_EXECUTION_ROUTE_NOT_VERIFIED"))
    return out
