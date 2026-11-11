"""Research-only restoration of a prospective archive into EMPTY directories.

Rejects path traversal, missing/extra files, checksum mismatches and non-empty
destinations. No remote storage or live scanner interaction.
"""
import json
from pathlib import Path
from zipfile import ZipFile
from research_prospective_archive import verify_archive


def restore_archive(archive_path, destination):
    verification = verify_archive(archive_path)
    destination = Path(destination)
    if destination.exists() and any(destination.iterdir()):
        raise ValueError("destination_not_empty")
    with ZipFile(archive_path, "r") as archive:
        manifest = json.loads(archive.read("manifest.json"))
        # Verification runs before creating any files.
        if not verification["valid"]:
            raise ValueError("invalid_archive")
        destination.mkdir(parents=True, exist_ok=True)
        for folder in ("candidates", "outcomes"):
            (destination / folder).mkdir(exist_ok=True)
        for item in manifest["files"]:
            target = destination / item["path"]
            target.write_bytes(archive.read(item["path"]))
    return {"research_only": True, "trade_ready": False,
            "restored_files": len(manifest["files"]),
            "candidate_directory": str(destination / "candidates"),
            "outcome_directory": str(destination / "outcomes")}
