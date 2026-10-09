"""Finnhub Europe access probe. No token is ever logged; no trading signals."""
import json,os,urllib.parse,urllib.request,urllib.error
from datetime import datetime,timezone
from pathlib import Path
OUT=Path("reports");OUT.mkdir(exist_ok=True)
SYMBOLS=["EDPR.LS","ASML.AS","SAP.DE","SAN.PA","PRY.MI","AZN.L"]
def request(endpoint,params,token):
    url="https://finnhub.io/api/v1/"+endpoint+"?"+urllib.parse.urlencode(params)
    req=urllib.request.Request(url,headers={"X-Finnhub-Token":token,"Accept":"application/json","User-Agent":"DipsausResearch/1.0"})
    try:
        with urllib.request.urlopen(req,timeout=12) as response:
            return {"http_status":response.status,"body":json.load(response)}
    except urllib.error.HTTPError as e:
        return {"http_status":e.code,"error":"HTTP_"+str(e.code)}
    except Exception as e:
        return {"error":type(e).__name__}
def main():
    token=os.environ.get("FINNHUB_API_KEY","").strip()
    report={"generated_utc":datetime.now(timezone.utc).isoformat(),"provider":"Finnhub",
      "status":"NOT_CONFIGURED" if not token else "SOURCE_ACCESS_PROBE",
      "note":"No provider result becomes a live executable quote; ticker identity, exchange, currency and broker bid/ask remain unverified.",
      "trade_ready":False,"results":[]}
    if token:
        # Control quote distinguishes an invalid/blocked key from Europe-only entitlement.
        control=request("quote",{"symbol":"AAPL"},token)
        control_body=control.pop("body",None)
        control_ok=(control.get("http_status")==200 and isinstance(control_body,dict)
                    and isinstance(control_body.get("c"),(int,float)) and control_body["c"]>0)
        report["control"]={"symbol":"AAPL","http_status":control.get("http_status"),
                           "valid_price_returned":control_ok}
        report["status"]="CONTROL_PASSED" if control_ok else "CONTROL_BLOCKED"
        if not control_ok:
            report["diagnosis"]="US control failed: cannot attribute European 403 to Europe-only market permissions. Verify key/account/API access."
        for symbol in SYMBOLS:
            response=request("quote",{"symbol":symbol},token)
            body=response.pop("body",None)
            row={"symbol_candidate":symbol,**response,"identity_verified":False,"currency_verified":False,
                 "broker_quote_verified":False,"trade_ready":False}
            if isinstance(body,dict):
                price=body.get("c");stamp=body.get("t")
                age=datetime.now(timezone.utc).timestamp()-stamp if isinstance(stamp,(int,float)) and stamp>0 else None
                row.update(price=price if isinstance(price,(int,float)) and price>0 else None,
                           quote_utc=datetime.fromtimestamp(stamp,timezone.utc).isoformat() if age is not None else None,
                           age_seconds=round(age,1) if age is not None else None,
                           provider_freshness_pass=age is not None and 0<=age<=120 and isinstance(price,(int,float)) and price>0,
                           provider_error=str(body.get("error",""))[:120] or None)
            report["results"].append(row)
            print(json.dumps(row),flush=True)
        europe_403=all(r.get("http_status")==403 for r in report["results"])
        if control_ok and europe_403:
            report["diagnosis"]="US control works; all European requests denied. Likely exchange entitlement or unsupported symbol scheme; verify Finnhub symbol mappings before purchasing access."
        report["status"]="EUROPE_403_CONTROL_OK" if control_ok and europe_403 else report["status"]
    (OUT/"europe_finnhub_probe.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
    print("FINNHUB_PROBE_STATUS="+report["status"])
if __name__=="__main__":main()

