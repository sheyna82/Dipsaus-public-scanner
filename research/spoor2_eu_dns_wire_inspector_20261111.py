"""Strict offline DNS wireformat response inspection; never establishes DNSSEC trust."""
import hashlib
import struct

def _name(packet, offset):
    labels=[]
    visited=set()
    end=None
    while True:
        if offset>=len(packet) or offset in visited:
            raise ValueError("invalid name offset or compression cycle")
        visited.add(offset)
        length=packet[offset]
        if length & 0xc0 == 0xc0:
            if offset+1>=len(packet):
                raise ValueError("truncated pointer")
            pointer=((length & 0x3f)<<8)|packet[offset+1]
            if pointer>=offset:
                raise ValueError("pointer outside packet")
            if end is None: end=offset+2
            offset=pointer
            continue
        if length & 0xc0 or length>63:
            raise ValueError("invalid label")
        offset+=1
        if length==0:
            if end is None: end=offset
            break
        if offset+length>len(packet):
            raise ValueError("truncated label")
        labels.append(packet[offset:offset+length].lower())
        if sum(map(len,labels))+len(labels)>255:
            raise ValueError("oversized name")
        offset+=length
    return b".".join(labels).decode("ascii"),end

def inspect_dns_wire_response(payload, *, expected_name, expected_type=1, expected_id=None):
    base={"status":"BLOCKED","dnssec_verified":False,"dns_admitted":False,
          "connection_authorized":False,"trade_ready":False,"order_placement_enabled":False}
    if not isinstance(payload,bytes) or not 12<=len(payload)<=65535:
        return {**base,"blocks":["INVALID_DNS_PACKET_LENGTH"]}
    if not isinstance(expected_name,str) or not expected_name or len(expected_name)>253:
        return {**base,"blocks":["INVALID_EXPECTED_QUESTION"]}
    if type(expected_type) is not int or not 1<=expected_type<=65535:
        return {**base,"blocks":["INVALID_EXPECTED_QUESTION"]}
    if expected_id is not None and (type(expected_id) is not int or not 0<=expected_id<=65535):
        return {**base,"blocks":["INVALID_EXPECTED_ID"]}
    try:
        txid,flags,qd,an,ns,ar=struct.unpack("!HHHHHH",payload[:12])
        if expected_id is not None and txid!=expected_id:
            return {**base,"blocks":["DNS_TRANSACTION_ID_MISMATCH"]}
        if (not flags & 0x8000 or flags & 0x7800 or flags & 0x0200 or
            flags & 0x000f or flags & 0x0040 or flags & 0x0010):
            return {**base,"blocks":["DNS_RESPONSE_FLAGS_REJECTED"]}
        if qd!=1:
            return {**base,"blocks":["DNS_QUESTION_COUNT_REJECTED"]}
        name,pos=_name(payload,12)
        if pos+4>len(payload):
            raise ValueError("truncated question")
        qtype,qclass=struct.unpack("!HH",payload[pos:pos+4])
        if name!=expected_name.rstrip(".").lower() or qtype!=expected_type or qclass!=1:
            return {**base,"blocks":["DNS_QUESTION_MISMATCH"]}
        pos+=4
        for _ in range(an+ns+ar):
            _,pos=_name(payload,pos)
            if pos+10>len(payload):
                raise ValueError("truncated resource record")
            rtype,rclass,ttl,rdlength=struct.unpack("!HHIH",payload[pos:pos+10])
            pos+=10
            if pos+rdlength>len(payload):
                raise ValueError("truncated rdata")
            pos+=rdlength
        if pos!=len(payload):
            return {**base,"blocks":["DNS_TRAILING_BYTES"]}
    except (ValueError,UnicodeDecodeError,struct.error):
        return {**base,"blocks":["MALFORMED_DNS_WIRE_RESPONSE"]}
    return {**base,"status":"DNS_WIREFORMAT_PARSED_ONLY",
            "record_sha256":hashlib.sha256(payload).hexdigest(),
            "answer_count":an,"authority_count":ns,"additional_count":ar,
            "resolver_ad_claim":bool(flags & 0x0020),
            "checking_disabled":bool(flags & 0x0010),
            "blocks":["DNSSEC_NOT_LOCALLY_VALIDATED","RESOLVER_NOT_AUTHENTICATED",
                      "DNS_EVIDENCE_NOT_ADMITTED"]}
