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
    def test_ds_missing_digest_rejected(self):
        a=rr(43,address=bytes.fromhex("12340802"))
        self.assertEqual(inspect(packet(answer=a),expected_name="example.com")["blocks"],["INVALID_DNSSEC_RECORD_STRUCTURE"])
    def test_dnskey_missing_key_rejected(self):
        a=rr(48,address=bytes.fromhex("01000308"))
        self.assertEqual(inspect(packet(answer=a),expected_name="example.com")["blocks"],["INVALID_DNSSEC_RECORD_STRUCTURE"])
    def test_rrsig_short_header_rejected(self):
        a=rr(46,address=bytes(18))
        self.assertEqual(inspect(packet(answer=a),expected_name="example.com")["blocks"],["INVALID_DNSSEC_RECORD_STRUCTURE"])
    def test_dnssec_record_parse_does_not_verify(self):
        a=rr(43,address=bytes.fromhex("12340802")+bytes(32))
        result=inspect(packet(answer=a),expected_name="example.com")
        self.assertEqual(result["status"],"DNS_WIREFORMAT_PARSED_ONLY")
        self.assertFalse(result["dnssec_verified"])
        self.assertFalse(result["dns_admitted"])
    def test_ds_wrong_digest_size_rejected(self):
        a=rr(43,address=bytes.fromhex("12340802")+bytes(31))
        self.assertEqual(inspect(packet(answer=a),expected_name="example.com")["blocks"],["INVALID_DNSSEC_RECORD_STRUCTURE"])
    def test_ds_unknown_digest_type_rejected(self):
        a=rr(43,address=bytes.fromhex("12340863")+bytes(32))
        self.assertEqual(inspect(packet(answer=a),expected_name="example.com")["blocks"],["INVALID_DNSSEC_RECORD_STRUCTURE"])
    def test_dnskey_invalid_protocol_rejected(self):
        a=rr(48,address=bytes.fromhex("01000208ff"))
        self.assertEqual(inspect(packet(answer=a),expected_name="example.com")["blocks"],["INVALID_DNSSEC_RECORD_STRUCTURE"])
    def test_dnskey_protocol_three_not_verified(self):
        a=rr(48,address=bytes.fromhex("01000308ff"))
        result=inspect(packet(answer=a),expected_name="example.com")
        self.assertEqual(result["status"],"DNS_WIREFORMAT_PARSED_ONLY")
        self.assertFalse(result["dnssec_verified"])
    def test_rrsig_missing_signature_rejected(self):
        header=struct.pack("!HBBIIIH",1,8,2,60,1000,500,123)
        a=rr(46,address=header+bytes.fromhex("00"))
        self.assertEqual(inspect(packet(answer=a),expected_name="example.com")["blocks"],["INVALID_DNSSEC_RECORD_STRUCTURE"])
    def test_rrsig_compressed_signer_rejected(self):
        header=struct.pack("!HBBIIIH",1,8,2,60,1000,500,123)
        a=rr(46,address=header+bytes.fromhex("c00c01"))
        self.assertEqual(inspect(packet(answer=a),expected_name="example.com")["blocks"],["INVALID_DNSSEC_RECORD_STRUCTURE"])
    def test_rrsig_valid_structure_still_unverified(self):
        header=struct.pack("!HBBIIIH",1,8,2,60,1000,500,123)
        a=rr(46,address=header+bytes.fromhex("00aabb"))
        result=inspect(packet(answer=a),expected_name="example.com")
        self.assertEqual(result["status"],"DNS_WIREFORMAT_PARSED_ONLY")
        self.assertFalse(result["dnssec_verified"])
    def test_rrsig_missing_type_covered_rejected(self):
        header=struct.pack("!HBBIIIH",0,8,2,60,1000,500,123)
        a=rr(46,address=header+bytes.fromhex("00aabb"))
        self.assertEqual(inspect(packet(answer=a),expected_name="example.com")["blocks"],["INVALID_DNSSEC_RECORD_STRUCTURE"])
    def test_cd_flag_rejected(self):
        self.assertEqual(inspect(packet(flags=0x8190),expected_name="example.com")["blocks"],["DNS_RESPONSE_FLAGS_REJECTED"])
    def test_reserved_z_flag_rejected(self):
        self.assertEqual(inspect(packet(flags=0x81c0),expected_name="example.com")["blocks"],["DNS_RESPONSE_FLAGS_REJECTED"])
    def test_tc_flag_rejected(self):
        self.assertEqual(inspect(packet(flags=0x8380),expected_name="example.com")["blocks"],["DNS_RESPONSE_FLAGS_REJECTED"])
    def test_servfail_rejected(self):
        self.assertEqual(inspect(packet(flags=0x8182),expected_name="example.com")["blocks"],["DNS_RESPONSE_FLAGS_REJECTED"])
if __name__=="__main__": unittest.main()
