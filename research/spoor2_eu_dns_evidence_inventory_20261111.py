"""Offline DNS RR evidence inventory. Informational only; never admits DNS or trading."""
import hashlib
import struct

def inventory_dns_rr_evidence(packet, *, expected_name=None, expected_type=None, expected_id=None, max_records=256, max_total_rdata_bytes=32768):
    blocked={"status":"BLOCKED","dnssec_verified":False,"dns_admitted":False,
             "connection_authorized":False,"trade_ready":False,"order_placement_enabled":False}
    if type(packet) is not bytes or not 12<=len(packet)<=65535:
        return {**blocked,"blocks":["INVALID_PACKET"]}
    if type(max_records) is not int or not 1<=max_records<=4096:
        return {**blocked,"blocks":["INVALID_RECORD_LIMIT"]}
    if type(max_total_rdata_bytes) is not int or not 1<=max_total_rdata_bytes<=65535:
        return {**blocked,"blocks":["INVALID_RDATA_BUDGET"]}
    if expected_name is not None and (not isinstance(expected_name,str) or not expected_name or len(expected_name)>253):
        return {**blocked,"blocks":["INVALID_EXPECTED_QUESTION"]}
    if expected_type is not None and (type(expected_type) is not int or not 1<=expected_type<=65535):
        return {**blocked,"blocks":["INVALID_EXPECTED_QUESTION"]}
    if expected_id is not None and (type(expected_id) is not int or not 0<=expected_id<=65535):
        return {**blocked,"blocks":["INVALID_EXPECTED_ID"]}
    try:
        from research.spoor2_eu_dns_wire_inspector_20261111 import _name
        txid,flags,qd,an,ns,ar=struct.unpack_from("!HHHHHH",packet)
        if an+ns+ar>max_records:
            return {**blocked,"blocks":["DNS_RECORD_LIMIT_EXCEEDED"]}
        if (not flags & 0x8000 or flags & 0x0200 or flags & 0x7800 or
            flags & 0x000f or flags & 0x0040 or flags & 0x0010 or qd!=1):
            return {**blocked,"blocks":["INVALID_HEADER"]}
        if expected_id is not None and txid!=expected_id:
            return {**blocked,"blocks":["DNS_TRANSACTION_ID_MISMATCH"]}
        question_name,pos=_name(packet,12)
        if pos+4>len(packet): raise ValueError("question")
        question_type,question_class=struct.unpack_from("!HH",packet,pos)
        if question_class!=1: raise ValueError("question class")
        if ((expected_name is not None and question_name!=expected_name.rstrip(".").lower()) or
            (expected_type is not None and question_type!=expected_type)):
            return {**blocked,"blocks":["DNS_QUESTION_MISMATCH"]}
        pos+=4
        records=[]
        total_rdata_bytes=0
        for section,count in (("answer",an),("authority",ns),("additional",ar)):
            for _ in range(count):
                record_start=pos
                owner,pos=_name(packet,pos)
                if pos+10>len(packet): raise ValueError("rr header")
                kind,cls,ttl,size=struct.unpack_from("!HHIH",packet,pos)
                pos+=10
                if pos+size>len(packet): raise ValueError("rdata")
                total_rdata_bytes+=size
                if total_rdata_bytes>max_total_rdata_bytes:
                    return {**blocked,"blocks":["DNS_RDATA_BUDGET_EXCEEDED"]}
                records.append({"section":section,"owner":owner,"type":kind,
                                "class":cls,"ttl":ttl,"rdata_length":size,
                                "wire_start":record_start,"wire_end":pos+size,
                                "rdata_start":pos,"rdata_end":pos+size,
                                "wire_sha256":hashlib.sha256(packet[record_start:pos+size]).hexdigest(),
                                "rdata_sha256":hashlib.sha256(packet[pos:pos+size]).hexdigest()})
                pos+=size
        if pos!=len(packet): raise ValueError("trailing")
    except (ValueError,UnicodeDecodeError,struct.error,ImportError):
        return {**blocked,"blocks":["MALFORMED_PACKET"]}
    return {**blocked,"status":"EVIDENCE_INVENTORY_ONLY",
            "packet_sha256":hashlib.sha256(packet).hexdigest(),
            "question":{"name":question_name,"type":question_type,"class":question_class},
            "records":records,
            "total_rdata_bytes":total_rdata_bytes,
            "blocks":["DNSSEC_NOT_CRYPTOGRAPHICALLY_VERIFIED","SOURCE_NOT_AUTHENTICATED"]}
