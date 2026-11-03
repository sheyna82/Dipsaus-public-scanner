"""Offline, bounded GitHub ZIP-to-inventory bridge; no network or side effects."""
import hashlib
import io
import json
import tempfile
import zipfile
from pathlib import Path
from research_finnhub_observation_inventory import build_inventory

MAX_ZIP_BYTES = 65536
MAX_JSON_BYTES = 8192
MEMBER = "source-observation.json"

def inventory_from_artifact(archive, *, expected_zip_sha256):
    if not isinstance(expected_zip_sha256, str) or len(expected_zip_sha256) != 64:
        raise ValueError("expected_zip_digest_required")
    try:
        int(expected_zip_sha256, 16)
    except ValueError as exc:
        raise ValueError("expected_zip_digest_required") from exc
    archive = Path(archive)
    if not archive.is_file() or archive.stat().st_size > MAX_ZIP_BYTES:
        raise ValueError("zip_size_invalid")
    with archive.open("rb") as stream:
        raw = stream.read(MAX_ZIP_BYTES + 1)
    if len(raw) > MAX_ZIP_BYTES:
        raise ValueError("zip_size_invalid")
    if hashlib.sha256(raw).hexdigest() != expected_zip_sha256.lower():
        raise ValueError("zip_hash_mismatch")
    try:
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            infos = z.infolist()
            if len(infos) != 1 or infos[0].filename != MEMBER:
                raise ValueError("unexpected_zip_members")
            info = infos[0]
            if (info.is_dir() or info.flag_bits & 1 or info.file_size > MAX_JSON_BYTES
                    or info.compress_size > MAX_ZIP_BYTES or info.compress_type not in
                    (zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED)):
                raise ValueError("unsafe_zip_member")
            if info.external_attr >> 16 & 0o170000 not in (0, 0o100000):
                raise ValueError("unsafe_zip_member")
            with z.open(info) as stream:
                payload = stream.read(MAX_JSON_BYTES + 1)
            if len(payload) != info.file_size or len(payload) > MAX_JSON_BYTES:
                raise ValueError("unsafe_zip_member")
    except (zipfile.BadZipFile, RuntimeError, EOFError) as exc:
        raise ValueError("invalid_zip_archive") from exc
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / MEMBER
        path.write_bytes(payload)
        inventory = build_inventory([path])
    return {"zip_sha256": hashlib.sha256(raw).hexdigest(),
            "observation_json_sha256": hashlib.sha256(payload).hexdigest(),
            "inventory": inventory,
            "research_only": True, "trade_ready": False}
