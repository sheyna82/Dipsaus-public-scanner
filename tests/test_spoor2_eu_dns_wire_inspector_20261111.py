import struct
import unittest
from research.spoor2_eu_dns_wire_inspector_20261111 import inspect_dns_wire_response as inspect

def packet(flags=0x8180,qd=1,tail=b"",answer=b""):
    q=b"\x07example\x03com\x00"+struct.pack("!HH",1,1)
    return struct.pack("!HHHHHH",42,flags,qd,1 if answer else 0,0,0)+q+answer+tail

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
    def test_tc_flag_rejected(self):
        self.assertEqual(inspect(packet(flags=0x8380),expected_name="example.com")["blocks"],["DNS_RESPONSE_FLAGS_REJECTED"])
    def test_servfail_rejected(self):
        self.assertEqual(inspect(packet(flags=0x8182),expected_name="example.com")["blocks"],["DNS_RESPONSE_FLAGS_REJECTED"])
if __name__=="__main__": unittest.main()
