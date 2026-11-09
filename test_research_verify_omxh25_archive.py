"""Offline archive verifier tests: synthetic bytes never pass official digest."""
import io
import json
import unittest
import zipfile
from unittest.mock import patch
from research_verify_omxh25_archive import verify, EXPECTED

def synthetic_archive(mutate=False):
    pdfs={name:b"%PDF-1.7\\nsynthetic "+name.encode() for name in EXPECTED}
    docs=[{"filename":name,"sha256":__import__("hashlib").sha256(raw).hexdigest(),"size_bytes":len(raw)} for name,raw in pdfs.items()]
    manifest={"schema":"dipsaus-official-source-archive-v1","research_only":True,"trade_ready":False,"documents":docs}
    if mutate:manifest["trade_ready"]=True
    stream=io.BytesIO()
    with zipfile.ZipFile(stream,"w") as z:
        for name,raw in pdfs.items():z.writestr(name,raw)
        z.writestr("manifest.json",json.dumps(manifest))
    stream.seek(0)
    return stream

class Tests(unittest.TestCase):
    def test_synthetic_pdf_never_passes_official_hash(self):
        with self.assertRaisesRegex(ValueError,"ARCHIVE_PDF_INTEGRITY_INVALID"):
            verify(synthetic_archive())
    def test_trading_promotion_is_rejected(self):
        with self.assertRaisesRegex(ValueError,"ARCHIVE_RESEARCH_CONTRACT_INVALID"):
            verify(synthetic_archive(mutate=True))
    def test_unexpected_member_is_rejected(self):
        stream=synthetic_archive()
        other=io.BytesIO()
        with zipfile.ZipFile(stream) as source,zipfile.ZipFile(other,"w") as dest:
            for name in source.namelist():dest.writestr(name,source.read(name))
            dest.writestr("untrusted.txt","extra")
        other.seek(0)
        with self.assertRaisesRegex(ValueError,"ARCHIVE_MEMBERS_INVALID"):
            verify(other)
if __name__=="__main__":unittest.main()
