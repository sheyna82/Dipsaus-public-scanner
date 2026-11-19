"""Isolated EU OHLCV research capture; no trading decisions or orders.
Usage: python research_capture_europe_history.py OUTPUT.json
All source URLs are fixed; instrument identity is checked fail-closed.
"""
import hashlib,json,math,urllib.parse,urllib.request
from datetime import datetime,timezone
from pathlib import Path
SYMBOLS=("ASML.AS","IFX.DE","NOKIA.HE","RHM.DE")
MAX_BYTES=2000000
class NoRedirects(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,req,fp,code,msg,headers,newurl):
        raise ValueError("redirect_forbidden")
def collect(destination,fetch=None):
    destination=Path(destination)
    if destination.exists():raise FileExistsError("immutable_capture_exists")
    if not destination.parent.is_dir():raise ValueError("destination_directory_missing")
    fetch=fetch or urllib.request.build_opener(NoRedirects()).open
    result={"schema":"dipsaus_europe_research_history_v1","captured_utc":datetime.now(timezone.utc).isoformat(),
            "research_only":True,"trade_ready":False,"degiro_instrument_verified":False,"series":{}}
    for symbol in SYMBOLS:
        url="https://query1.finance.yahoo.com/v8/finance/chart/"+symbol+"?"+urllib.parse.urlencode(
            {"range":"6mo","interval":"1d","includePrePost":"false"})
        req=urllib.request.Request(url,headers={"Accept":"application/json","User-Agent":"DipsausResearchCapture/1.0"})
        with fetch(req,timeout=20) as response:
            if response.status!=200:raise ValueError("http_error:"+symbol)
            raw=response.read(MAX_BYTES+1)
        if not raw or len(raw)>MAX_BYTES:raise ValueError("response_size_invalid:"+symbol)
        doc=json.loads(raw,parse_constant=lambda _: (_ for _ in ()).throw(ValueError("nonfinite")))
        data=doc["chart"]["result"][0]
        if data["meta"].get("symbol")!=symbol:raise ValueError("symbol_mismatch:"+symbol)
        ts=data["timestamp"];q=data["indicators"]["quote"][0]
        keys=("open","high","low","close","volume")
        if any(len(q[k])!=len(ts) for k in keys):raise ValueError("length_mismatch:"+symbol)
        bars=[]
        for i,t in enumerate(ts):
            v=[q[k][i] for k in keys]
            if any(x is None or isinstance(x,bool) or not isinstance(x,(int,float)) or not math.isfinite(x) for x in v):continue
            o,h,l,c,vol=v
            if min(o,h,l,c)<=0 or l>min(o,c) or h<max(o,c) or vol<0:continue
            bars.append({"t":int(t),**dict(zip(keys,v))})
        if len(bars)<100 or any(x["t"]>=y["t"] for x,y in zip(bars,bars[1:])):
            raise ValueError("invalid_bars:"+symbol)
        result["series"][symbol]={"source":url,"source_sha256":hashlib.sha256(raw).hexdigest(),
            "count":len(bars),"bars":bars}
    with destination.open("x",encoding="utf-8") as out:
        json.dump(result,out,sort_keys=True,separators=(",",":"));out.write("\n")
    return {"status":"research_capture_complete","counts":{k:v["count"] for k,v in result["series"].items()},"trade_ready":False}
if __name__=="__main__":
    import sys
    if len(sys.argv)!=2:raise SystemExit("usage: python research_capture_europe_history.py OUTPUT")
    print(json.dumps(collect(sys.argv[1]),sort_keys=True))
