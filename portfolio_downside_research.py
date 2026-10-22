"""Fail-closed research-only intraday downside observation."""
import math

def evaluate_intraday_downside(closes, highs, lows, opens, *, enabled=False):
    if not enabled:
        return {'status':'DISABLED','trigger':False}
    n=len(closes)
    if n<31 or any(len(series)!=n for series in (highs,lows,opens)):
        return {'status':'INSUFFICIENT_DATA','trigger':False}
    try:
        series=[[float(v) for v in s] for s in (closes,highs,lows,opens)]
        if any(not math.isfinite(v) or v<=0 for s in series for v in s):
            return {'status':'INVALID_DATA','trigger':False}
        c,h,l,o=series
        if any(lo>min(op,cl) or hi<max(op,cl) or lo>hi for cl,hi,lo,op in zip(c,h,l,o)):
            return {'status':'INVALID_OHLC','trigger':False}
        drawdown=(c[-1]/max(h)-1)*100
        lower_low=l[-1]<min(l[-31:-1])
        red=sum(c[-i]<o[-i] for i in range(1,6))
        trigger=drawdown<=-2 and lower_low and red>=3
        return {'status':'RESEARCH_ONLY','trigger':trigger,'drawdown_pct':round(drawdown,3),'lower_low':lower_low,'red_last5':red}
    except (TypeError,ValueError,OverflowError):
        return {'status':'INVALID_DATA','trigger':False}
