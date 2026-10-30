"""Merge shard summaries without treating repeated event horizons as independent trades."""
import argparse,glob,json
from pathlib import Path

def aggregate(paths):
    reports=[];duplicates=[];seen=set();all_rows=[]
    for p in paths:
        obj=json.loads(Path(p).read_text())
        reports.append({"file":str(p),"selected":obj["selected_symbols"],"success":obj["successful_symbols"],"linked_events":obj["linked_events"]})
        if obj["selected_symbols"] != len(obj["results"]): raise ValueError("selected_count_mismatch")
        if obj["successful_symbols"] != sum(x["status"]=="downloaded_unverified" for x in obj["results"]): raise ValueError("success_count_mismatch")
        if obj["linked_events"] != sum(x["event_count"] for x in obj["results"] if x["status"]=="downloaded_unverified"): raise ValueError("linked_event_count_mismatch")
        for item in obj["results"]:
            if item["symbol"] in seen:duplicates.append(item["symbol"])
            seen.add(item["symbol"])
    if duplicates:raise ValueError(f"overlapping_shards:{duplicates[:10]}")
    return {"shards":len(reports),"symbols_attempted":sum(x["selected"] for x in reports),"symbols_with_prices":sum(x["success"] for x in reports),"linked_event_records":sum(x["linked_events"] for x in reports),"distinct_symbols":len(seen),"nonempty_shards":sum(x["selected"]>0 for x in reports),"empty_shards":sum(x["selected"]==0 for x in reports),"timestamp_verified":False,"trade_ready":False,"shard_reports":reports}

def main():
    p=argparse.ArgumentParser();p.add_argument("--root",required=True);p.add_argument("--output",required=True);p.add_argument("--require-shards",type=int,default=20)
    a=p.parse_args()
    paths=sorted(Path(a.root).rglob("linkage_report.json"))
    if len(paths)!=a.require_shards:raise ValueError(f"incomplete_shards:{len(paths)}/{a.require_shards}")
    result=aggregate(paths)
    Path(a.output).write_text(json.dumps(result,indent=2))
    print(json.dumps({k:v for k,v in result.items() if k!="shard_reports"}))
if __name__=="__main__":main()
