"""Offline, read-only EXE 1-minute replay. No secrets, pushes, or portfolio changes."""
import argparse
import csv
import json
from datetime import datetime
from pathlib import Path
from portfolio_downside_research import replay_intraday

REQUIRED=('timestamp','open','high','low','close')

def load_session(path, session):
    rows=[]
    with open(path,newline='',encoding='utf-8-sig') as f:
        reader=csv.DictReader(f)
        if not reader.fieldnames or any(k not in reader.fieldnames for k in REQUIRED):
            raise ValueError('Missing required columns')
        for item in reader:
            ts=datetime.fromisoformat(item['timestamp'].replace('Z','+00:00'))
            if ts.tzinfo is None:
                raise ValueError('Timezone-aware timestamps required')
            if ts.date().isoformat()!=session:
                continue
            rows.append((ts,{k:float(item[k]) for k in REQUIRED[1:]}))
    if not rows:
        raise ValueError('No rows for requested session')
    if any(rows[i][0]>=rows[i+1][0] for i in range(len(rows)-1)):
        raise ValueError('Timestamps must be strictly increasing')
    if any((rows[i+1][0]-rows[i][0]).total_seconds()!=60 for i in range(len(rows)-1)):
        raise ValueError('Incomplete one-minute session: gaps or duplicate bars')
    return rows

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--csv',required=True,type=Path)
    p.add_argument('--session',default='2026-10-22')
    args=p.parse_args()
    rows=load_session(args.csv,args.session)
    result=replay_intraday([bar for _,bar in rows],enabled=True)
    first=result['first_signal_index']
    print(json.dumps({'session':args.session,'bars':len(rows),'status':result['status'],
                      'first_signal_utc':rows[first][0].isoformat() if first is not None else None,
                      'signal_minutes':result['signal_count']},sort_keys=True))

if __name__=='__main__':
    main()
