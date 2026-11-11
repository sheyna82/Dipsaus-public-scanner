"""Offline DNS RR evidence inventory. Informational only; never admits DNS or trading."""
import hashlib
import struct

def inventory_dns_rr_evidence(packet):
    blocked={"status":"BLOCKED","dnssec_verified":False,"dns_admitted":False,
             "connection_authorized":False,"trade_ready":False,"order_placement_enabled":False}
    if type(packet) is not bytes or not 12<=len(packet)<=65535:
        return {**blocked,"blocks":["INVALID_PACKET"]}
    try:
        from research.spoor2_eu_dns_wire_inspector_20261111 import _name
        txid,flags,qd,an,ns,ar=struct.unpack_from("!HHHHHH",packet)
        if (not flags & 0x8000 or flags & 0x0200 or flags & 0x7800 or
            flags & 0x000f or flags & 0x0040 or flags & 0x0010 or qd!=1):
            return {**blocked,"blocks":["INVALID_HEADER"]}
        question_name,pos=_name(packet,12)
        if pos+4>len(packet): raise ValueError("question")
        question_type,question_class=struct.unpack_from("!HH",packet,pos)
        if question_class!=1: raise ValueError("question class")
        pos+=4
        records=[]
        for section,count in (("answer",an),("authority",ns),("additional",ar)):
            for _ in range(count):
                owner,pos=_name(packet,pos)
                if pos+10>len(packet): raise ValueError("rr header")
                kind,cls,ttl,size=struct.unpack_from("!HHIH",packet,pos)
                pos+=10
                if pos+size>len(packet): raise ValueError("rdata")
                records.append({"section":section,"owner":owner,"type":kind,
                                "class":cls,"ttl":ttl,"rdata_length":size,
                                "rdata_sha256":hashlib.sha256(packet[pos:pos+size]).hexdigest()})
                pos+=size
        if pos!=len(packet): raise ValueError("trailing")
    except (ValueError,UnicodeDecodeError,struct.error,ImportError):
        return {**blocked,"blocks":["MALFORMED_PACKET"]}
    return {**blocked,"status":"EVIDENCE_INVENTORY_ONLY",
            "packet_sha256":hashlib.sha256(packet).hexdigest(),
            "question":{"name":question_name,"type":question_type,"class":question_class},
            "records":records,
            "blocks":["DNSSEC_NOT_CRYPTOGRAPHICALLY_VERIFIED","SOURCE_NOT_AUTHENTICATED"]}
