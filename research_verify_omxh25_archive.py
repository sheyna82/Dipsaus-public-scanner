"""Offline verification of a user-retained OMXH25 evidence ZIP. No network, no trading."""
import hashlib
import json
import zipfile
from pathlib import Path

EXPECTED={
 "nasdaq-index-versions.pdf":"52f35d3e0d4500e01d116c135628c3e145de0b3929e3532c37f3a59d79f550ef",
 "nasdaq-methodology.pdf":"41c43c502b6862606aef255a55cef41ccc8ff606b21f8b32975edb48fe6b12a2",
}
def verify(path):
    with zipfile.ZipFile(Path(path)) as archive:
        names=archive.namelist()
        if len(names)!=3 or set(names)!=set(EXPECTED)|{"manifest.json"}:
            raise ValueError("ARCHIVE_MEMBERS_INVALID")
        if any(archive.getinfo(n).file_size>500_000 for n in names):
            raise ValueError("ARCHIVE_MEMBER_TOO_LARGE")
        manifest=json.loads(archive.read("manifest.json"))
        if manifest.get("schema")!="dipsaus-official-source-archive-v1" or manifest.get("research_only") is not True or manifest.get("trade_ready") is not False:
            raise ValueError("ARCHIVE_RESEARCH_CONTRACT_INVALID")
        docs=manifest.get("documents")
        if not isinstance(docs,list) or len(docs)!=2 or {d.get("filename") for d in docs}!=set(EXPECTED):
            raise ValueError("ARCHIVE_MANIFEST_INVALID")
        for doc in docs:
            name=doc["filename"]
            raw=archive.read(name)
            if not raw.startswith(b"%PDF-") or hashlib.sha256(raw).hexdigest()!=EXPECTED[name] or doc.get("sha256")!=EXPECTED[name] or doc.get("size_bytes")!=len(raw):
                raise ValueError("ARCHIVE_PDF_INTEGRITY_INVALID:"+name)
        return {"status":"verified_original_bytes","research_only":True,"trade_ready":False,"files":len(EXPECTED)}
if __name__=="__main__":
    import sys
    if len(sys.argv)!=2:raise SystemExit("usage: python research_verify_omxh25_archive.py EVIDENCE.zip")
    print(json.dumps(verify(sys.argv[1]),sort_keys=True))
