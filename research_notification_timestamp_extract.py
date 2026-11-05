"""Offline extraction of notification UTC timestamps from private state.

Do not upload raw private state to a public repository or GitHub artifacts.
Only return a minimal, explicitly selected symbol/time record in memory.
"""
from datetime import datetime, timezone

def verified_notification_times(state, symbols):
    if not isinstance(state,dict) or not isinstance(state.get("signals"),dict):
        raise ValueError("invalid_state")
    selected=set(symbols)
    if not selected or any(not isinstance(s,str) or not s for s in selected):
        raise ValueError("invalid_symbols")
    output=[]
    for key,record in state["signals"].items():
        if not isinstance(record,dict):
            continue
        parts=key.split("|")
        matches=[symbol for symbol in selected if symbol in parts]
        if len(matches)!=1:
            continue
        raw=record.get("notified_utc")
        if not isinstance(raw,str):
            continue
        try:
            dt=datetime.fromisoformat(raw.replace("Z","+00:00"))
        except ValueError:
            continue
        if dt.tzinfo is None:
            continue
        output.append({"symbol":matches[0],
                       "notification_utc":dt.astimezone(timezone.utc).isoformat(),
                       "delivery_status":record.get("delivery","unknown"),
                       "key_family":parts[0],
                       "execution_verified":False,
                       "research_only":True})
    return sorted(output,key=lambda x:(x["notification_utc"],x["symbol"]))
