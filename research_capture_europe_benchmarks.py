"""Fail-closed European benchmark daily capture, isolated research only.

Benchmark choices: AEX price index, DAX price index, OMX Helsinki 25,
STOXX Europe 600 price index. Provider aliases are *candidates* and must
be validated against provider metadata; unsupported aliases block capture.
"""
import hashlib,json,math,urllib.parse,urllib.request
from datetime import datetime,timezone
from pathlib import Path

# Explicit research aliases. Never silently substitute a total-return index.
BENCHMARKS={"AEX":"^AEX","DAX_PRICE":"^GDAXIP","OMXH25":"^OMXH25","STOXX600_PRICE":"^STOXX"}
MAX_BYTES=2000000
class NoRedirects(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,req,fp,code,msg,headers,newurl):raise ValueError("redirect_forbidden")
def collect(destination,fetch=None):
    p=Path(destination)
    if p.exists():raise FileExistsError("immutable_capture_exists")
    if not p.parent.is_dir():raise ValueError("destination_directory_missing")
    fetch=fetch or urllib.request.build_opener(NoRedirects()).open
    out={"schema":"dipsaus_europe_benchmark_research_v1","captured_utc":datetime.now(timezone.utc).isoformat(),
         "research_only":True,"trade_ready":False,"benchmark_identity_verified":False,"series":{}}
    for name,symbol in BENCHMARKS.items():
        url="https://query1.finance.yahoo.com/v8/finance/chart/"+urllib.parse.quote(symbol,safe="")+"?"+urllib.parse.urlencode(
            {"range":"6mo","interval":"1d","includePrePost":"false"})
        req=urllib.request.Request(url,headers={"Accept":"application/json","User-Agent":"DipsausResearchCapture/1.0"})
        with fetch(req,timeout=20) as response:
            if response.status!=200:raise ValueError("http_error:"+name)
            raw=response.read(MAX_BYTES+1)
        if not raw or len(raw)>MAX_BYTES:raise ValueError("response_size_invalid:"+name)
        doc=json.loads(raw,parse_constant=lambda _: (_ for _ in ()).throw(ValueError("nonfinite")))
        data=doc["chart"]["result"][0]
        if data["meta"].get("symbol")!=symbol:raise ValueError("symbol_mismatch:"+name)
        timestamps=data["timestamp"];quotes=data["indicators"]["quote"][0]
        if len(quotes["close"])!=len(timestamps):raise ValueError("length_mismatch:"+name)
        bars=[]
        for t,c in zip(timestamps,quotes["close"]):
            if c is None or isinstance(c,bool) or not isinstance(c,(int,float)) or not math.isfinite(c) or c<=0:continue
            bars.append({"t":int(t),"close":c})
        if len(bars)<100 or any(a["t"]>=b["t"] for a,b in zip(bars,bars[1:])):
            raise ValueError("invalid_bars:"+name)
        out["series"][name]={"provider_symbol":symbol,"source":url,"source_sha256":hashlib.sha256(raw).hexdigest(),
                             "count":len(bars),"bars":bars}
    out["benchmark_identity_verified"]=True
    with p.open("x",encoding="utf-8") as f:json.dump(out,f,sort_keys=True,separators=(",",":"));f.write("\n")
    return {"status":"research_capture_complete","counts":{k:v["count"] for k,v in out["series"].items()},"trade_ready":False}
if __name__=="__main__":
    import sys
    if len(sys.argv)!=2:raise SystemExit("usage: python research_capture_europe_benchmarks.py OUTPUT")
    print(json.dumps(collect(sys.argv[1]),sort_keys=True))
