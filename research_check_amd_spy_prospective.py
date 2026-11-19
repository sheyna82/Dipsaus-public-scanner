"""Research-only, fail-closed AMD/SPY end-of-session protocol check."""
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

PROTOCOL_SHA256="27bc6a2bf6e80b4df41faaee53726622f23f1ab495ffcd412639548d025536ee"
THRESHOLDS={"relative_strength_20d_pct":-4.34385,"volume_ratio_20d":0.88975,"atr_14_pct":4.25095}
START="2026-11-09"
def day(bar):
    return datetime.fromtimestamp(bar["t"],timezone.utc).astimezone(ZoneInfo("America/New_York")).date().isoformat()
def evaluate(amd,spy,now=None):
    now=now or datetime.now(timezone.utc)
    if now.tzinfo is None: raise ValueError("NAIVE_CLOCK")
    ny=now.astimezone(ZoneInfo("America/New_York"))
    if ny.hour<17: raise ValueError("REGULAR_SESSION_NOT_CLOSED")
    if amd.get("symbol")!="AMD" or spy.get("symbol")!="SPY": raise ValueError("SYMBOL_MISMATCH")
    if amd.get("research_only") is not True or spy.get("research_only") is not True: raise ValueError("NOT_RESEARCH_ONLY")
    a=amd["series"]["daily"]["bars"]; s=spy["bars"]
    sa={day(b):b for b in s}
    if len(sa)!=len(s) or len({day(b) for b in a})!=len(a): raise ValueError("DUPLICATE_SESSION")
    matched=[(day(b),b,sa[day(b)]) for b in a if day(b) in sa]
    if len(matched)<35: raise ValueError("INSUFFICIENT_OVERLAP")
    dates=[x[0] for x in matched]
    if dates!=sorted(dates): raise ValueError("UNSORTED_DATES")
    target=ny.date().isoformat()
    if dates[-1]!=target or target<START or ny.weekday()>4: raise ValueError("NO_FRESH_PROSPECTIVE_SESSION")
    _,cur,sp=matched[-1]
    prev20=matched[-21][1]; spy20=matched[-21][2]
    rs=100*((cur["close"]/prev20["close"]-1)-(sp["close"]/spy20["close"]-1))
    vol=cur["volume"]/(sum(x[1]["volume"] for x in matched[-21:-1])/20)
    trs=[]
    for i in range(len(matched)-14,len(matched)):
        b=matched[i][1]; p=matched[i-1][1]["close"]
        trs.append(max(b["high"]-b["low"],abs(b["high"]-p),abs(b["low"]-p)))
    atr=100*sum(trs)/14/cur["close"]
    features={"relative_strength_20d_pct":rs,"volume_ratio_20d":vol,"atr_14_pct":atr}
    if any(not math.isfinite(v) for v in features.values()): raise ValueError("NONFINITE_FEATURE")
    checks={"relative_strength_20d_pct":rs>=THRESHOLDS["relative_strength_20d_pct"],
            "volume_ratio_20d":vol>=THRESHOLDS["volume_ratio_20d"],
            "atr_14_pct":atr<=THRESHOLDS["atr_14_pct"]}
    # A filter pass alone is NOT a pattern-qualified signal or trade approval.
    return {"schema":"dipsaus_amd_spy_prospective_check_v1","date":target,
            "protocol_sha256":PROTOCOL_SHA256,"research_only":True,"trade_ready":False,
            "features":features,"checks":checks,"all_feature_checks_pass":all(checks.values()),
            "pattern_eligibility_verified":False,"decision":"RESEARCH_ONLY_NOT_TRADE_READY",
            "amd_source_sha256":amd["series"]["daily"]["source_sha256"],
            "spy_source_sha256":spy["source_sha256"]}
if __name__=="__main__":
    import sys
    if len(sys.argv)!=4: raise SystemExit("usage: check.py AMD_JSON SPY_JSON OUTPUT_JSON")
    result=evaluate(json.loads(Path(sys.argv[1]).read_text()),json.loads(Path(sys.argv[2]).read_text()))
    output=Path(sys.argv[3])
    with output.open("x") as f: json.dump(result,f,sort_keys=True,indent=2)
    print(json.dumps({"date":result["date"],"decision":result["decision"],"all_feature_checks_pass":result["all_feature_checks_pass"]}))
