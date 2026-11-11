import hashlib
import struct
import unittest
from research.spoor2_eu_dns_evidence_inventory_20261111 import inventory_dns_rr_evidence as inventory

def packet(*, record=b"", count=0, trailing=b""):
    q=bytes.fromhex("076578616d706c6503636f6d00")+struct.pack("!HH",1,1)
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
    def test_question_metadata_preserved(self):
        x=inventory(packet())
        self.assertEqual(x["question"],{"name":"example.com","type":1,"class":1})
        self.assertFalse(x["dns_admitted"])
    def test_checking_disabled_flag_rejected(self):
        raw=bytearray(packet())
        raw[3]|=0x10
        self.assertEqual(inventory(bytes(raw))["blocks"],["INVALID_HEADER"])
    def test_reserved_flag_rejected(self):
        raw=bytearray(packet())
        raw[3]|=0x40
        self.assertEqual(inventory(bytes(raw))["blocks"],["INVALID_HEADER"])
    def test_packet_hash_covers_full_original_wire_bytes(self):
        raw=packet(record=rr(kind=48,rdata=bytes.fromhex("01000308ff")),count=1)
        result=inventory(raw)
        self.assertEqual(result["packet_sha256"],hashlib.sha256(raw).hexdigest())
        self.assertEqual(result["records"][0]["type"],48)
        self.assertFalse(result["dnssec_verified"])
    def test_record_order_is_preserved(self):
        raw=packet(record=rr(kind=43,rdata=b"first")+rr(kind=46,rdata=b"second"),count=2)
        result=inventory(raw)
        self.assertEqual([item["type"] for item in result["records"]],[43,46])
        self.assertEqual(result["records"][1]["rdata_sha256"],hashlib.sha256(b"second").hexdigest())
        self.assertFalse(result["connection_authorized"])
    def test_forward_owner_pointer_fails_closed(self):
        malformed=bytes.fromhex("c0ff")+struct.pack("!HHIH",43,1,30,4)+b"test"
        self.assertEqual(inventory(packet(record=malformed,count=1))["status"],"BLOCKED")
    def test_declared_extra_record_fails_closed(self):
        self.assertEqual(inventory(packet(record=rr(),count=2))["status"],"BLOCKED")
    def test_matching_expected_question_and_transaction(self):
        x=inventory(packet(),expected_name="EXAMPLE.COM.",expected_type=1,expected_id=7)
        self.assertEqual(x["status"],"EVIDENCE_INVENTORY_ONLY")
        self.assertFalse(x["dnssec_verified"])
    def test_wrong_expected_name_blocks(self):
        self.assertEqual(inventory(packet(),expected_name="other.example")["blocks"],["DNS_QUESTION_MISMATCH"])
    def test_wrong_expected_type_blocks(self):
        self.assertEqual(inventory(packet(),expected_type=28)["blocks"],["DNS_QUESTION_MISMATCH"])
    def test_wrong_expected_transaction_blocks(self):
        self.assertEqual(inventory(packet(),expected_id=8)["blocks"],["DNS_TRANSACTION_ID_MISMATCH"])
    def test_boolean_expected_transaction_blocks(self):
        self.assertEqual(inventory(packet(),expected_id=True)["blocks"],["INVALID_EXPECTED_ID"])
    def test_nonbinary_input_fails_closed(self):
        self.assertEqual(inventory("not bytes")["status"],"BLOCKED")
    def test_duplicate_records_retained_as_observations(self):
        x=inventory(packet(record=rr()+rr(),count=2))
        self.assertEqual(len(x["records"]),2)
        self.assertFalse(x["dnssec_verified"])

if __name__=="__main__":
    unittest.main()
