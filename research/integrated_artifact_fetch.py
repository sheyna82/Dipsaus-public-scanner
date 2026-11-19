"""Download frozen GitHub Actions artifact safely; research-only, no live dependencies.

Requires GH_TOKEN with actions:read for private artifacts. Never prints the token.
"""
import hashlib
import io
import json
import os
from pathlib import Path
import urllib.request
import zipfile

REPO = "sheyna82/Dipsaus-public-scanner"
ARTIFACT_ID = 13428010951
ZIP_SHA256 = "10a99a373e1d054267c4053c8f9dfb9315dbf28789d7dc5e1763c5faba6ea82a"
ALLOWED = {
    "candidate_feature_oos.json": "bae59b8c9143aab47ebbffa18b2f9f619d2fd80281ad8c69a42e27a0283cdcbd",
    "candidate_feature_oos_input_snapshot.json": "622785a4705e7ffc60e10ca61e36f04389f516408c1d7132dda9f5c79d629c0e",
    "candidate_feature_portfolio_quarters.json": "830c886e6283c1cfbce2c1a169529e9593fa7f7a305e053aaef861af70b97d61",
}

def verify_zip(raw):
    if hashlib.sha256(raw).hexdigest() != ZIP_SHA256:
        raise ValueError("ARTIFACT_ZIP_HASH_MISMATCH")
    verified = {}
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        names = archive.namelist()
        if len(names) != len(set(names)):
            raise ValueError("DUPLICATE_ZIP_ENTRY")
        for item in archive.infolist():
            name = item.filename
            if name not in ALLOWED or item.is_dir() or item.file_size > 30_000_000:
                raise ValueError("UNEXPECTED_ZIP_ENTRY:" + name)
            data = archive.read(item)
            if hashlib.sha256(data).hexdigest() != ALLOWED[name]:
                raise ValueError("ARTIFACT_FILE_HASH_MISMATCH:" + name)
            verified[name] = data
    if set(verified) != set(ALLOWED):
        raise ValueError("MISSING_ARTIFACT_FILES")
    return verified

def fetch_and_verify(destination):
    token = os.environ.get("GH_TOKEN")
    if not token:
        raise RuntimeError("GH_TOKEN_REQUIRED_FOR_ARTIFACT_DOWNLOAD")
    req = urllib.request.Request(
        f"https://api.github.com/repos/{REPO}/actions/artifacts/{ARTIFACT_ID}/zip",
        headers={"Authorization": "Bearer " + token,
                 "Accept": "application/vnd.github+json",
                 "X-GitHub-Api-Version": "2022-11-28"})
    with urllib.request.urlopen(req, timeout=30) as response:
        if response.geturl().split("/")[0] not in ("https:",):
            raise ValueError("INSECURE_ARTIFACT_REDIRECT")
        raw = response.read(60_000_001)
    if len(raw) > 60_000_000:
        raise ValueError("ARTIFACT_TOO_LARGE")
    verified = verify_zip(raw)
    dest = Path(destination)
    dest.mkdir(parents=True, exist_ok=True)
    for name, data in verified.items():
        (dest / name).write_bytes(data)
    return {"status": "RESEARCH_ONLY_ARTIFACT_VERIFIED",
            "artifact_id": ARTIFACT_ID, "files": sorted(verified),
            "trade_ready": False}

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        raise SystemExit("usage: integrated_artifact_fetch.py DESTINATION_DIRECTORY")
    print(json.dumps(fetch_and_verify(sys.argv[1]), sort_keys=True))
