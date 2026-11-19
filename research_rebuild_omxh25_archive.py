"""Rebuild and verify a research-only Nasdaq OMXH25 archive from a captured Actions artifact.

Offline only. A matching PDF digest establishes captured bytes, not provider identity.
"""
import argparse
import base64
import hashlib
import json
import zipfile
from pathlib import Path

from research_verify_omxh25_archive import EXPECTED, verify

CAPTURE_MEMBERS = {
    "nasdaq-index-versions.json": "nasdaq-index-versions.pdf",
    "nasdaq-methodology.json": "nasdaq-methodology.pdf",
}


def rebuild(capture_zip, output_zip, expected_artifact_sha256=None):
    capture_zip, output_zip = Path(capture_zip), Path(output_zip)
    if capture_zip.resolve() == output_zip.resolve():
        raise ValueError("INPUT_OUTPUT_SAME_PATH")
    artifact_digest = hashlib.sha256(capture_zip.read_bytes()).hexdigest()
    if expected_artifact_sha256 and artifact_digest != expected_artifact_sha256:
        raise ValueError("CAPTURE_ARTIFACT_HASH_MISMATCH")
    pdfs = {}
    with zipfile.ZipFile(capture_zip) as captured:
        names = captured.namelist()
        if len(names) != len(CAPTURE_MEMBERS) or set(names) != set(CAPTURE_MEMBERS):
            raise ValueError("CAPTURE_MEMBERS_INVALID")
        for json_name, pdf_name in CAPTURE_MEMBERS.items():
            if captured.getinfo(json_name).file_size > 600_000:
                raise ValueError("CAPTURE_MEMBER_TOO_LARGE")
            record = json.loads(captured.read(json_name))
            if (record.get("research_only") is not True
                    or record.get("trade_ready") is not False
                    or record.get("independently_audited") is not False):
                raise ValueError("CAPTURE_RESEARCH_CONTRACT_INVALID")
            raw = base64.b64decode(record["official_document_base64"], validate=True)
            digest = hashlib.sha256(raw).hexdigest()
            if not raw.startswith(b"%PDF-") or digest != EXPECTED[pdf_name]:
                raise ValueError("CAPTURE_PDF_HASH_MISMATCH:" + pdf_name)
            if record.get("official_document_sha256") != digest:
                raise ValueError("CAPTURE_RECEIPT_MISMATCH:" + pdf_name)
            pdfs[pdf_name] = raw
    manifest = {
        "schema": "dipsaus-official-source-archive-v1",
        "research_only": True,
        "trade_ready": False,
        "documents": [
            {"filename": name, "sha256": hashlib.sha256(raw).hexdigest(), "size_bytes": len(raw)}
            for name, raw in pdfs.items()
        ],
    }
    with zipfile.ZipFile(output_zip, "w", compression=zipfile.ZIP_DEFLATED) as output:
        for name, raw in pdfs.items():
            output.writestr(name, raw)
        output.writestr("manifest.json", json.dumps(manifest, sort_keys=True))
    return {
        "artifact_sha256": artifact_digest,
        "derived_zip_sha256": hashlib.sha256(output_zip.read_bytes()).hexdigest(),
        "verification": verify(output_zip),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("capture_zip")
    parser.add_argument("output_zip")
    parser.add_argument("--expected-artifact-sha256")
    args = parser.parse_args()
    print(json.dumps(rebuild(args.capture_zip, args.output_zip, args.expected_artifact_sha256), sort_keys=True))
