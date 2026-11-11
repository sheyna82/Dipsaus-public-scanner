import hashlib
import struct
import unittest
from research.spoor2_eu_dns_evidence_inventory_20261111 import inventory_dns_rr_evidence as inventory

def packet(*, record=b"", count=0, trailing=b""):
    q=b"\\x07example\\x03com\\x00"+struct.pack("!HH",1,1)
    return struct.pack("!HHHHHH",7,0x8180,1,count,0,0)+q+record+trailing

def rr(kind=43, rdata=b"test"):
    return bytes.fromhex("c00c")+struct.pack("!HHIH",kind,1,30,len(rdata))+rdata

class EvidenceInventoryTests(unittest.TestCase):
    def test_empty_response_inventory_only(self):
        x=inventory(packet())
        self.assertEqual(x["status"],"EVIDENCE_INVENTORY_ONLY")
        self.assertEqual(x["records"],[])
        self.assertFalse(x["dnssec_verified"])
        self.assertFalse(x["trade_ready"])
    def test_record_hash_and_type(self):
        x=inventory(packet(record=rr(),count=1))
        self.assertEqual(x["records"][0]["type"],43)
        self.assertEqual(x["records"][0]["rdata_sha256"],hashlib.sha256(b"test").hexdigest())
        self.assertFalse(x["dns_admitted"])
    def test_truncated_record_fails_closed(self):
        self.assertEqual(inventory(packet(record=rr()[:-1],count=1))["status"],"BLOCKED")
    def test_trailing_bytes_fails_closed(self):
        self.assertEqual(inventory(packet(trailing=b"x"))["status"],"BLOCKED")
    def test_nonbinary_input_fails_closed(self):
        self.assertEqual(inventory("not bytes")["status"],"BLOCKED")
    def test_duplicate_records_retained_as_observations(self):
        x=inventory(packet(record=rr()+rr(),count=2))
        self.assertEqual(len(x["records"]),2)
        self.assertFalse(x["dnssec_verified"])

if __name__=="__main__":
    unittest.main()
