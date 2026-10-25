"""Portable research-only prospective ledger archive.

Builds a deterministic ZIP snapshot and manifest for download as a GitHub Actions
artifact. An artifact is not permanent storage; retention must be managed
separately. This module never commits data to the repository.
"""
import hashlib
import json
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED


def archive_ledger(candidate_dir, outcome_dir, destination):
    destination = Path(destination)
    if destination.exists():
        raise FileExistsError("archive_already_exists")
    entries = []
    for category, directory in (("candidates", candidate_dir), ("outcomes", outcome_dir)):
        directory = Path(directory)
        if not directory.is_dir():
            raise ValueError("ledger_directory_missing")
        for path in sorted(directory.glob("*.json")):
            raw = path.read_bytes()
            json.loads(raw)
            entries.append({"path": f"{category}/{path.name}",
                            "sha256": hashlib.sha256(raw).hexdigest(),
                            "bytes": len(raw), "raw": raw})
    manifest = {"research_only": True, "trade_ready": False,
                "format_version": 1,
                "files": [{key: item[key] for key in ("path", "sha256", "bytes")}
                          for item in entries]}
    with ZipFile(destination, "x", compression=ZIP_DEFLATED) as archive:
        for item in entries:
            archive.writestr(item["path"], item["raw"])
        archive.writestr("manifest.json", json.dumps(manifest, sort_keys=True, indent=2) + "\n")
    return {"archive": str(destination), "entry_count": len(entries),
            "research_only": True, "trade_ready": False,
            "sha256": hashlib.sha256(destination.read_bytes()).hexdigest()}


def verify_archive(path):
    with ZipFile(path, "r") as archive:
        names = archive.namelist()
        if len(names) != len(set(names)):
            raise ValueError("duplicate_archive_member")
        manifest = json.loads(archive.read("manifest.json"))
        for item in manifest["files"]:
            name = item["path"]
            if not name.startswith(("candidates/", "outcomes/")) or ".." in Path(name).parts:
                raise ValueError("unsafe_archive_path")
            raw = archive.read(name)
            if hashlib.sha256(raw).hexdigest() != item["sha256"]:
                raise ValueError("archive_hash_mismatch")
            if len(raw) != item["bytes"]:
                raise ValueError("archive_size_mismatch")
        expected = {"manifest.json"} | {item["path"] for item in manifest["files"]}
        if set(names) != expected:
            raise ValueError("unexpected_archive_member")
    return {"valid": True, "file_count": len(manifest["files"]),
            "research_only": True}
