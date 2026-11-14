"""Isolated SPY benchmark daily capture. Research only, no signal or orders."""
import hashlib
import json
import math
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

BASE = "https://query1.finance.yahoo.com/v8/finance/chart/SPY"
MAX_BYTES = 2_000_000

class NoRedirects(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ValueError("redirect_forbidden")

def collect(destination, fetch=None):
    destination = Path(destination)
    if destination.exists():
        raise FileExistsError("immutable_capture_exists")
    if not destination.parent.is_dir():
        raise ValueError("destination_directory_missing")
    fetch = fetch or urllib.request.build_opener(NoRedirects()).open
    url = BASE + "?" + urllib.parse.urlencode({"range":"6mo","interval":"1d","includePrePost":"false"})
    request = urllib.request.Request(url, headers={"Accept":"application/json","User-Agent":"DipsausResearchCapture/1.0"})
    with fetch(request, timeout=20) as response:
        if response.status != 200:
            raise ValueError("http_error")
        raw = response.read(MAX_BYTES+1)
    if not raw or len(raw)>MAX_BYTES:
        raise ValueError("response_size_invalid")
    doc = json.loads(raw, parse_constant=lambda _: (_ for _ in ()).throw(ValueError("nonfinite")))
    result = doc["chart"]["result"][0]
    if result["meta"].get("symbol")!="SPY":
        raise ValueError("symbol_mismatch")
    ts = result["timestamp"]
    quote = result["indicators"]["quote"][0]
    if any(len(quote[k])!=len(ts) for k in ("open","high","low","close","volume")):
        raise ValueError("bar_length_mismatch")
    bars=[]
    for i,t in enumerate(ts):
        vals=[quote[k][i] for k in ("open","high","low","close","volume")]
        if any(v is None or isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) for v in vals):
            continue
        o,h,l,c,v=vals
        if min(o,h,l,c)<=0 or l>min(o,c) or h<max(o,c) or v<0:
            continue
        bars.append({"t":int(t),"open":o,"high":h,"low":l,"close":c,"volume":v})
    if len(bars)<100 or any(a["t"]>=b["t"] for a,b in zip(bars,bars[1:])):
        raise ValueError("insufficient_or_unsorted_bars")
    out={"schema":"dipsaus_spy_history_v1","symbol":"SPY","captured_utc":datetime.now(timezone.utc).isoformat(),
         "research_only":True,"trade_ready":False,"source":url,"source_sha256":hashlib.sha256(raw).hexdigest(),
         "count":len(bars),"bars":bars}
    with destination.open("x",encoding="utf-8") as f:
        json.dump(out,f,sort_keys=True,separators=(",",":"))
        f.write("\n")
    return {"status":"research_capture_complete","count":len(bars),"trade_ready":False}

if __name__=="__main__":
    import sys
    if len(sys.argv)!=2:
        raise SystemExit("usage: python research_capture_spy_history.py OUTPUT")
    print(json.dumps(collect(sys.argv[1]),sort_keys=True))
