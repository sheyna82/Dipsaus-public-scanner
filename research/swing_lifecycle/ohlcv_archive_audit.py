"""Read-only OHLCV JSONL(.gz) archive inventory; no network or orders."""
import argparse
import gzip
import json
import math
from collections import Counter
from datetime import date
from pathlib import Path

def audit_archive(path):
    path=Path(path)
    opener=gzip.open if path.suffix==".gz" else open
    symbols=set()
    issues=Counter()
    first=None
    last=None
    total_bars=0
    per_symbol={}
    with opener(path,"rt",encoding="utf-8") as stream:
        for lineno,line in enumerate(stream,1):
            if not line.strip():continue
            try:
                record=json.loads(line)
                symbol=record["symbol"]
                bars=record["bars"]
                if not isinstance(symbol,str) or not symbol or not isinstance(bars,list):
                    raise ValueError("invalid record")
            except (ValueError,KeyError,TypeError):
                issues["INVALID_RECORD"]+=1
                continue
            if symbol in symbols:issues["DUPLICATE_SYMBOL_RECORD"]+=1
            symbols.add(symbol)
            seen=set()
            previous=None
            valid=0
            for bar in bars:
                try:
                    day=date.fromisoformat(bar[0])
                    o,h,l,c,v=bar[1:6]
                    if not all(isinstance(x,(int,float)) and not isinstance(x,bool) for x in (o,h,l,c,v)):
                        raise ValueError("nonnumeric")
                    if not all(math.isfinite(x) for x in (o,h,l,c,v)) or not (0<l<=min(o,c)<=max(o,c)<=h and v>=0):
                        raise ValueError("bad OHLCV")
                except (ValueError,TypeError,IndexError,AttributeError):
                    issues["INVALID_BAR"]+=1
                    continue
                if day in seen:issues["DUPLICATE_SESSION"]+=1
                if previous is not None and day<=previous:issues["NONINCREASING_SESSION"]+=1
                seen.add(day)
                previous=day
                valid+=1
                first=min(first,day) if first else day
                last=max(last,day) if last else day
            total_bars+=valid
            per_symbol[symbol]=valid
    return {"archive":str(path),"unique_symbols":len(symbols),"valid_bars":total_bars,
            "first_session":first.isoformat() if first else None,
            "last_session":last.isoformat() if last else None,
            "symbols_under_150_bars":sum(n<150 for n in per_symbol.values()),
            "issues":dict(sorted(issues.items())),
            "limitations":"Does not infer missing market sessions without exchange calendars; no split/dividend, delisting, currency, or independent provenance verification."}

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("archives",nargs="+")
    args=parser.parse_args()
    for path in args.archives:
        print(json.dumps(audit_archive(path),sort_keys=True))
if __name__=="__main__":main()
