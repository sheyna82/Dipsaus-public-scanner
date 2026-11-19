"""Offline ISO 10383 dataset-byte intake; no network, registry or trade attestation.

Validates a supplied XLSX container and computes a reproducible digest.
This cannot establish that the bytes originated at the ISO registration authority.
"""
import hashlib
import io
import zipfile
from xml.etree import ElementTree as ET

MAX_BYTES = 20_000_000
MAX_UNCOMPRESSED = 100_000_000
MAX_MEMBERS = 1000
XLSX_NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"


def inspect_iso_mic_xlsx(data):
    out = dict(status="BLOCKED", sha256=None, xlsx_container_valid=False,
               source_attested=False, mic_registered=False,
               trade_ready=False, order_placement_enabled=False, blocks=[])
    if not isinstance(data, bytes) or not data or len(data) > MAX_BYTES:
        out["blocks"].append("INVALID_OR_OVERSIZED_DATASET")
        return out
    out["sha256"] = hashlib.sha256(data).hexdigest()
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            names = z.namelist()
            if len(names) != len(set(names)) or len(names) > MAX_MEMBERS:
                out["blocks"].append("DUPLICATE_OR_EXCESSIVE_ZIP_MEMBERS")
                return out
            if any(n.startswith("/") or "\\" in n or ".." in n.split("/")
                   for n in names):
                out["blocks"].append("UNSAFE_ZIP_MEMBER_PATH")
                return out
            if sum(i.file_size for i in z.infolist()) > MAX_UNCOMPRESSED:
                out["blocks"].append("EXCESSIVE_UNCOMPRESSED_SIZE")
                return out
            if "[Content_Types].xml" not in names or "xl/workbook.xml" not in names:
                out["blocks"].append("NOT_AN_XLSX_WORKBOOK")
                return out
            xml = z.read("xl/workbook.xml")
            if b"<!DOCTYPE" in xml or b"<!ENTITY" in xml:
                out["blocks"].append("UNSAFE_WORKBOOK_XML")
                return out
            root = ET.fromstring(xml)
            if root.tag != XLSX_NS + "workbook":
                out["blocks"].append("INVALID_WORKBOOK_ROOT")
                return out
            out["xlsx_container_valid"] = True
    except (zipfile.BadZipFile, OSError, ValueError, ET.ParseError, RuntimeError,
            NotImplementedError, KeyError):
        out["blocks"].append("INVALID_XLSX_CONTAINER")
        return out
    out["blocks"].extend(("OFFICIAL_DATASET_ORIGIN_NOT_ATTESTED",
                          "MIC_RECORDS_NOT_INDEPENDENTLY_VERIFIED"))
    return out
