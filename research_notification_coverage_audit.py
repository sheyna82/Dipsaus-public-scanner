"""Audit downloaded phone-signal OHLCV without inventing exact event timestamps.

Only use date-level coverage; screenshot clock times are not verified UTC.
"""
from datetime import datetime, timezone

SIGNAL_DAY = "2026-10-26"

def audit_coverage(cases, price_payloads, signal_day=SIGNAL_DAY):
    output=[]
    for case in cases:
        symbol=case.symbol
        payload=price_payloads.get(symbol)
        record={"symbol":symbol,"family":case.family,"signal_day":signal_day,
                "verified_signal_utc":False,"ready_for_forward_return":False,
                "ready_for_pre_signal_context":False,"research_only":True}
        if not payload:
            record["status"]="missing_price_file"
            output.append(record);continue
        bars=payload.get("bars",[])
        if not isinstance(bars,list):
            record["status"]="invalid_bars";output.append(record);continue
        dates=[]
        for bar in bars:
            try:
                ts=bar["timestamp"]
                if not isinstance(ts,int) or any(not isinstance(bar.get(k),(int,float)) or bar[k]<=0 for k in ("open","high","low","close")):
                    raise ValueError("bad_bar")
                dates.append(datetime.fromtimestamp(ts,timezone.utc).date().isoformat())
            except (KeyError,TypeError,ValueError,OverflowError,OSError):
                record["status"]="invalid_bars";break
        if "status" in record:
            output.append(record);continue
        if dates!=sorted(set(dates)):
            record["status"]="duplicate_or_unsorted_dates"
            output.append(record);continue
        before=sum(d<signal_day for d in dates)
        after=sum(d>signal_day for d in dates)
        record.update(status="daily_data_unverified",bars=len(bars),
                      bars_before_signal_day=before,bars_after_signal_day=after,
                      ready_for_pre_signal_context=before>=20,
                      last_date=dates[-1] if dates else None)
        # The actual signal time, exchange calendar, and executable spread remain unverified.
        output.append(record)
    return output
