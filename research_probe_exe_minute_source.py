"""One bounded, research-only EXE Yahoo 1m availability check; no retries."""
import json
import urllib.error
import urllib.request
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

URL="https://query1.finance.yahoo.com/v8/finance/chart/EXE?range=5d&interval=1m"
NY=ZoneInfo("America/New_York")

def probe(opener=urllib.request.urlopen):
    request=urllib.request.Request(URL,headers={"User-Agent":"DipsausResearchSourceCheck/1.0"})
    try:
        with opener(request,timeout=12) as response:
            data=json.load(response)
        result=data["chart"]["result"][0]
        timestamps=result.get("timestamp") or []
        quote=result["indicators"]["quote"][0]
        dates={}
        times={}
        invalid_ohlc=0
        for i,t in enumerate(timestamps):
            day=datetime.fromtimestamp(t,timezone.utc).astimezone(NY).date().isoformat()
            if all(i<len(quote.get(k,[])) and quote[k][i] is not None for k in ("open","high","low","close")):
                dates[day]=dates.get(day,0)+1
                times.setdefault(day,[]).append(datetime.fromtimestamp(t,timezone.utc).astimezone(NY))
                if not (quote["low"][i]<=min(quote["open"][i],quote["close"][i])<=max(quote["open"][i],quote["close"][i])<=quote["high"][i]):
                    invalid_ohlc+=1
        target=times.get("2026-10-22",[])
        gaps=sum((target[i+1]-target[i]).total_seconds()!=60 for i in range(len(target)-1))
        return {"status":"SOURCE_RESPONSE","symbol":"EXE","interval":"1m",
                "bars_by_ny_session":dates,
                "target_first_ny":target[0].isoformat() if target else None,
                "target_last_ny":target[-1].isoformat() if target else None,
                "target_gap_count":gaps,"invalid_ohlc_bars":invalid_ohlc,"target_2026_10_22_bars":dates.get("2026-10-22",0),
                "trade_ready":False,"source_verified_for_replay":False}
    except urllib.error.HTTPError as e:
        return {"status":"HTTP_ERROR","http_status":e.code,"trade_ready":False}
    except (ValueError,KeyError,IndexError,TypeError,urllib.error.URLError,TimeoutError) as e:
        return {"status":"SOURCE_UNAVAILABLE","error_type":type(e).__name__,"trade_ready":False}

if __name__=="__main__":
    print(json.dumps(probe(),sort_keys=True))
