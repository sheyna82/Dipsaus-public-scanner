"""Read-only, size-bounded GitHub Actions artifact download for research.

Downloads a GitHub-generated outer ZIP, extracts exactly one expected inner
archive, verifies its checksummed manifest, and never overwrites an existing
destination. No live scanner access and no repository writes.
"""
import io
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen
from zipfile import ZipFile, BadZipFile

from research_prospective_archive import verify_archive


def download_previous_archive(repo, token, artifact_id, destination, *,
                              expected_member="synthetic-prospective-ledger.zip",
                              opener=urlopen, max_bytes=8_000_000):
    if not token:
        raise ValueError("github_token_required")
    if not isinstance(artifact_id, int) or artifact_id <= 0:
        raise ValueError("invalid_artifact_id")
    if len(repo.split("/")) != 2 or any(
        not part.replace("-", "").replace("_", "").isalnum()
        for part in repo.split("/")
    ):
        raise ValueError("invalid_repository")
    if "/" in expected_member or "\\" in expected_member or expected_member.startswith("."):
        raise ValueError("unsafe_expected_member")
    destination = Path(destination)
    if destination.exists():
        raise FileExistsError("destination_already_exists")
    if max_bytes < 1024:
        raise ValueError("invalid_size_limit")
    request = Request(
        f"https://api.github.com/repos/{repo}/actions/artifacts/{artifact_id}/zip",
        headers={"Accept": "application/vnd.github+json",
                 "Authorization": "Bearer " + token,
                 "X-GitHub-Api-Version": "2022-11-28",
                 "User-Agent": "DIPSAUS-research-read-only"})
    try:
        with opener(request, timeout=20) as response:
            payload = response.read(max_bytes + 1)
    except HTTPError as exc:
        # Report only the failing host, never signed URLs or credentials.
        host = urlsplit(exc.geturl()).hostname or 'unknown'
        if host not in {'api.github.com', 'github.com'}:
            host = 'external-artifact-host'
        raise RuntimeError(f'artifact_download_http_{exc.code}_at_{host}') from None
    if len(payload) > max_bytes:
        raise ValueError("outer_artifact_too_large")
    try:
        with ZipFile(io.BytesIO(payload)) as outer:
            names = outer.namelist()
            if names != [expected_member]:
                raise ValueError("unexpected_outer_artifact_contents")
            member = outer.getinfo(expected_member)
            if member.file_size > max_bytes:
                raise ValueError("inner_archive_too_large")
            inner = outer.read(member)
            if len(inner) > max_bytes:
                raise ValueError("inner_archive_too_large")
    except BadZipFile as exc:
        raise ValueError("invalid_outer_zip") from exc
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("xb") as handle:
        handle.write(inner)
    try:
        verified = verify_archive(destination)
    except Exception:
        destination.unlink()
        raise
    return {"research_only": True, "trade_ready": False,
            "downloaded_artifact_id": artifact_id,
            "verified_files": verified["file_count"],
            "cross_run_download_performed": True,
            "destination": str(destination)}
