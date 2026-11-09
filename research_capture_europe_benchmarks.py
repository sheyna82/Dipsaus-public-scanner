"""Fail-closed European benchmark daily capture, isolated research only.

Benchmark choices: AEX price index, DAX price index, OMX Helsinki 25,
STOXX Europe 600 price index. Provider aliases are *candidates* and must
be validated against provider metadata; unsupported aliases block capture.
"""
import hashlib,json,math,urllib.parse,urllib.request
from datetime import datetime,timezone
from zoneinfo import ZoneInfo
from pathlib import Path

# Explicit research aliases. Never silently substitute a total-return index.
BENCHMARKS={"AEX":"^AEX","DAX_PRICE":"^GDAXIP","OMXH25":"^OMXH25","STOXX600_PRICE":"^STOXX"}
MAX_BYTES=2000000
class NoRedirects(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,req,fp,code,msg,headers,newurl):raise ValueError("redirect_forbidden")
def audit_omxh25_daily_bar(bar):
    """Interpret Yahoo's UTC bar label in Helsinki time; never approve identity."""
    t=bar.get("t")
    close=bar.get("close")
    if isinstance(t,bool) or not isinstance(t,int) or isinstance(close,bool) or not isinstance(close,(int,float)) or not math.isfinite(close) or close<=0:
        raise ValueError("invalid_omxh25_daily_bar")
    local=datetime.fromtimestamp(t,timezone.utc).astimezone(ZoneInfo("Europe/Helsinki"))
    # The observed Yahoo daily label corresponds to 10:00 Helsinki local time.
    # This is a *consistency check*, not proof of a close-time or index identity.
    return {"session_date":local.date().isoformat(),
            "label_utc":datetime.fromtimestamp(t,timezone.utc).isoformat(),
            "label_helsinki":local.isoformat(),
            "session_open_label_consistent":local.hour==10 and local.minute==0,
            "research_only":True,"identity_approved":False}

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
        meta=data["meta"]
        if meta.get("symbol")!=symbol:raise ValueError("symbol_mismatch:"+name)
        if meta.get("currency")!="EUR":raise ValueError("currency_not_eur:"+name)
        if meta.get("instrumentType")!="INDEX":raise ValueError("not_an_index:"+name)
        provider_meta={k:meta.get(k) for k in ("symbol","shortName","longName","currency","instrumentType","exchangeName","timezone","gmtoffset")}
        timestamps=data["timestamp"];quotes=data["indicators"]["quote"][0]
        if len(quotes["close"])!=len(timestamps):raise ValueError("length_mismatch:"+name)
        bars=[]
        for t,c in zip(timestamps,quotes["close"]):
            if c is None or isinstance(c,bool) or not isinstance(c,(int,float)) or not math.isfinite(c) or c<=0:continue
            bars.append({"t":int(t),"close":c})
        if len(bars)<100 or any(a["t"]>=b["t"] for a,b in zip(bars,bars[1:])):
            raise ValueError("invalid_bars:"+name)
        series={"provider_symbol":symbol,"source":url,"source_sha256":hashlib.sha256(raw).hexdigest(),
                "count":len(bars),"provider_metadata":provider_meta,"bars":bars}
        if name=="OMXH25":
            audits=[audit_omxh25_daily_bar(bar) for bar in bars]
            series["daily_label_audit"]={
                "schema":"omxh25_helsinki_label_audit_v1",
                "checked":len(audits),
                "consistent":sum(a["session_open_label_consistent"] for a in audits),
                "inconsistent_dates":[a["session_date"] for a in audits if not a["session_open_label_consistent"]],
                "research_only":True,"identity_approved":False}
        out["series"][name]=series
    out["benchmark_identity_verified"]=False  # Provider alias alone cannot verify official index variant or ISIN
    with p.open("x",encoding="utf-8") as f:json.dump(out,f,sort_keys=True,separators=(",",":"));f.write("\n")
    return {"status":"research_capture_complete","counts":{k:v["count"] for k,v in out["series"].items()},"trade_ready":False}
if __name__=="__main__":
    import sys
    if len(sys.argv)!=2:raise SystemExit("usage: python research_capture_europe_benchmarks.py OUTPUT")
    print(json.dumps(collect(sys.argv[1]),sort_keys=True))
