import struct
import unittest
from research.spoor2_eu_dns_wire_inspector_20261111 import inspect_dns_wire_response as inspect

def packet(flags=0x8180,qd=1,tail=b"",answer=b""):
    q=b"\x07example\x03com\x00"+struct.pack("!HH",1,1)
    return struct.pack("!HHHHHH",42,flags,qd,1 if answer else 0,0,0)+q+answer+tail


def rr(record_type, record_class=1, address=bytes.fromhex("01020304")):
    """Build an RR with a backward owner-name pointer and exact binary RDATA."""
    if not isinstance(address, bytes):
        raise TypeError("RDATA must be bytes")
    return bytes.fromhex("c00c")+struct.pack("!HHIH",record_type,record_class,30,len(address))+address

class DNSWireInspectorTests(unittest.TestCase):
    def test_normal_packet_is_not_admitted(self):
        r=inspect(packet(),expected_name="example.com",expected_id=42)
        self.assertEqual(r["status"],"DNS_WIREFORMAT_PARSED_ONLY")
        self.assertFalse(r["dnssec_verified"])
        self.assertFalse(r["dns_admitted"])
    def test_ad_flag_is_only_claim(self):
        r=inspect(packet(flags=0x81a0),expected_name="example.com")
        self.assertTrue(r["resolver_ad_claim"])
        self.assertFalse(r["dnssec_verified"])
    def test_wrong_question(self):
        self.assertEqual(inspect(packet(),expected_name="other.com")["blocks"],["DNS_QUESTION_MISMATCH"])
    def test_wrong_transaction(self):
        self.assertEqual(inspect(packet(),expected_name="example.com",expected_id=43)["blocks"],["DNS_TRANSACTION_ID_MISMATCH"])
    def test_truncated_packet(self):
        self.assertEqual(inspect(packet()[:15],expected_name="example.com")["blocks"],["MALFORMED_DNS_WIRE_RESPONSE"])
    def test_compression_cycle(self):
        p=struct.pack("!HHHHHH",42,0x8180,1,0,0,0)+b"\xc0\x0c"+struct.pack("!HH",1,1)
        self.assertEqual(inspect(p,expected_name="example.com")["blocks"],["MALFORMED_DNS_WIRE_RESPONSE"])
    def test_trailing_bytes(self):
        self.assertEqual(inspect(packet(tail=b"x"),expected_name="example.com")["blocks"],["DNS_TRAILING_BYTES"])
    def test_truncated_answer(self):
        a=b"\xc0\x0c"+struct.pack("!HHIH",1,1,30,4)+b"\x01"
        self.assertEqual(inspect(packet(answer=a),expected_name="example.com")["blocks"],["MALFORMED_DNS_WIRE_RESPONSE"])
    def test_forward_compression_pointer_rejected(self):
        p=struct.pack("!HHHHHH",42,0x8180,1,0,0,0)+b"\xc0\x0e\x00"+struct.pack("!HH",1,1)
        self.assertEqual(inspect(p,expected_name="example.com")["blocks"],["MALFORMED_DNS_WIRE_RESPONSE"])
    def test_a_record_wrong_length_rejected(self):
        a=b"\xc0\x0c"+struct.pack("!HHIH",1,1,30,3)+b"\x01\x02\x03"
        self.assertEqual(inspect(packet(answer=a),expected_name="example.com")["blocks"],["INVALID_ADDRESS_RECORD_STRUCTURE"])
    def test_aaaa_record_wrong_length_rejected(self):
        a=b"\xc0\x0c"+struct.pack("!HHIH",28,1,30,4)+b"\x01\x02\x03\x04"
        self.assertEqual(inspect(packet(answer=a),expected_name="example.com")["blocks"],["INVALID_ADDRESS_RECORD_STRUCTURE"])
    def test_a_record_wrong_class_rejected(self):
        a=b"\xc0\x0c"+struct.pack("!HHIH",1,3,30,4)+b"\x01\x02\x03\x04"
        self.assertEqual(inspect(packet(answer=a),expected_name="example.com")["blocks"],["INVALID_ADDRESS_RECORD_STRUCTURE"])
    def test_valid_a_record_still_not_admitted(self):
        a=b"\xc0\x0c"+struct.pack("!HHIH",1,1,30,4)+b"\x01\x02\x03\x04"
        r=inspect(packet(answer=a),expected_name="example.com")
        self.assertEqual(r["status"],"DNS_WIREFORMAT_PARSED_ONLY")
        self.assertFalse(r["dns_admitted"])
    def test_rr_fixture_is_binary_and_exact(self):
        a=rr(1)
        self.assertEqual(a,bytes.fromhex("c00c000100010000001e000401020304"))
        self.assertEqual(len(a),16)
    def test_cd_flag_rejected(self):
        self.assertEqual(inspect(packet(flags=0x8190),expected_name="example.com")["blocks"],["DNS_RESPONSE_FLAGS_REJECTED"])
    def test_reserved_z_flag_rejected(self):
        self.assertEqual(inspect(packet(flags=0x81c0),expected_name="example.com")["blocks"],["DNS_RESPONSE_FLAGS_REJECTED"])
    def test_tc_flag_rejected(self):
        self.assertEqual(inspect(packet(flags=0x8380),expected_name="example.com")["blocks"],["DNS_RESPONSE_FLAGS_REJECTED"])
    def test_servfail_rejected(self):
        self.assertEqual(inspect(packet(flags=0x8182),expected_name="example.com")["blocks"],["DNS_RESPONSE_FLAGS_REJECTED"])
if __name__=="__main__": unittest.main()
