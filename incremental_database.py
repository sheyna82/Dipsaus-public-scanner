"""Incremental bounded OHLCV collection; research data, not trade signals."""
import csv, gzip, hashlib, json, os, re, subprocess, tempfile, time, urllib.error, urllib.parse, urllib.request
from datetime import datetime, timezone
from pathlib import Path

BASE=Path("reports")
BASE.mkdir(exist_ok=True)
HEADERS={"User-Agent":"DipsausResearchPilot/0.2"}
REPO=os.getenv("GITHUB_REPOSITORY","owner/private-state-repository")
TOKEN=os.getenv("GITHUB_TOKEN","")
LIMIT=max(1,min(120,int(os.getenv("NEW_SYMBOL_LIMIT","120"))))

def get(url, authenticated=False):
    headers=dict(HEADERS)
    if authenticated and TOKEN:
        headers.update({"Authorization":"Bearer "+TOKEN,"Accept":"application/vnd.github+json","X-GitHub-Api-Version":"2022-11-28"})
    with urllib.request.urlopen(urllib.request.Request(url,headers=headers),timeout=30) as response:
        return response.read()

def universe():
    found=set()
    for index,url in enumerate(("https://www.nasdaqtrader.com/dynamic/SymDir/nasdaqlisted.txt",
                                "https://www.nasdaqtrader.com/dynamic/SymDir/otherlisted.txt")):
        raw=get(url).decode("utf-8-sig")
        rows=csv.DictReader((line for line in raw.splitlines() if not line.startswith("File Creation Time")),delimiter="|")
        for row in rows:
            symbol=row.get("Symbol" if index==0 else "ACT Symbol","").strip()
            name=row.get("Security Name","").lower()
            if row.get("Test Issue")!="N" or row.get("ETF")!="N" or not re.fullmatch(r"[A-Z]{1,5}",symbol):
                continue
            if any(term in name for term in ("warrant","rights","unit "," units","preferred","depositary","etn","exchange traded","notes due","bond","debenture")):
                continue
            found.add(symbol)
    return sorted(found,key=lambda symbol:hashlib.sha256(symbol.encode()).hexdigest())

def restore():
    """Restore latest cumulative artifact via GitHub CLI; fail closed if it cannot be read."""
    if not TOKEN:
        raise RuntimeError("GITHUB_TOKEN missing: cannot safely restore cumulative database")
    api="https://api.github.com/repos/"+REPO+"/actions/artifacts?per_page=100"
    artifacts=json.loads(get(api,True)).get("artifacts",[])
    candidates=[a for a in artifacts if not a.get("expired") and a.get("name") in
                ("ohlcv-incremental","database-pilot-60")]
    if not candidates:
        return {}, "no prior artifact (first run)"
    errors=[]
    for artifact in candidates:
        run_id=(artifact.get("workflow_run") or {}).get("id")
        if not run_id:
            errors.append(str(artifact.get("id"))+": missing workflow run ID")
            continue
        try:
            with tempfile.TemporaryDirectory() as folder:
                env=dict(os.environ,GH_TOKEN=TOKEN)
                result=subprocess.run(
                    ["gh","run","download",str(run_id),"-R",REPO,
                     "-n",artifact["name"],"-D",folder],
                    env=env,capture_output=True,text=True,timeout=90)
                if result.returncode:
                    raise RuntimeError(result.stderr.strip()[:250])
                paths=list(Path(folder).rglob("ohlcv.jsonl.gz"))
                if not paths:
                    paths=list(Path(folder).rglob("pilot_ohlcv.jsonl.gz"))
                if not paths:
                    raise RuntimeError("artifact contains no OHLCV database")
                records={}
                with gzip.open(paths[0],"rt",encoding="utf-8") as source:
                    for line in source:
                        entry=json.loads(line)
                        if isinstance(entry.get("symbol"),str) and isinstance(entry.get("bars"),list):
                            records[entry["symbol"]]=entry["bars"]
                if not records:
                    raise RuntimeError("artifact database empty")
                return records, "restored artifact "+str(artifact["id"])
        except Exception as error:
            errors.append(str(artifact.get("id"))+": "+str(error)[:250])
    raise RuntimeError("Prior artifacts exist but none could be restored: "+"; ".join(errors[:3]))

def bars(symbol):
    url="https://query1.finance.yahoo.com/v8/finance/chart/"+urllib.parse.quote(symbol,safe="")+"?range=1y&interval=1d"
    result=json.loads(get(url))["chart"]["result"][0]
    quote=result["indicators"]["quote"][0]
    rows=[]
    for index,stamp in enumerate(result.get("timestamp",[])):
        values=[quote[key][index] for key in ("open","high","low","close","volume")]
        if any(value is None for value in values):
            continue
        rows.append([datetime.fromtimestamp(stamp,timezone.utc).date().isoformat(),*values])
    return rows

def main():
    records,restore_note=restore()
    prior=len(records)
    symbols=universe()
    selected=[symbol for symbol in symbols if symbol not in records][:LIMIT]
    stats={"started_utc":datetime.now(timezone.utc).isoformat(),"universe_preliminary":len(symbols),
           "restored":prior,"restore_note":restore_note,"requested_new":len(selected),
           "attempted_new":0,"stored_new":0,"insufficient_history":[],"failed":[],
           "stopped_for_access_limit":False,"symbols_screened_for_recovery":0,"trade_ready":False,
           "warning":"Preliminary symbol filtering, unadjusted daily prices, no live trade quote."}
    try:
        for index,symbol in enumerate(selected):
            if index:
                time.sleep(1.5)
            stats["attempted_new"]+=1
            try:
                rows=bars(symbol)
                if len(rows)<150:
                    stats["insufficient_history"].append({"symbol":symbol,"valid_bars":len(rows)})
                    continue
                records[symbol]=rows
                stats["stored_new"]+=1
                print(symbol,"stored",len(rows),flush=True)
            except urllib.error.HTTPError as error:
                stats["failed"].append({"symbol":symbol,"http_status":error.code})
                if error.code in (401,403,429):
                    stats["stopped_for_access_limit"]=True
                    break
            except Exception as error:
                stats["failed"].append({"symbol":symbol,"error":type(error).__name__})
    finally:
        with gzip.open(BASE/"ohlcv.jsonl.gz","wt",encoding="utf-8") as output:
            for symbol in sorted(records):
                output.write(json.dumps({"symbol":symbol,"bars":records[symbol]})+"\n")
        stats["total_stored"]=len(records)
        stats["finished_utc"]=datetime.now(timezone.utc).isoformat()
        (BASE/"incremental_stats.json").write_text(json.dumps(stats,indent=2),encoding="utf-8")
        print(json.dumps(stats,indent=2),flush=True)
    eligible=stats["attempted_new"]-len(stats["insufficient_history"])
    if stats["stopped_for_access_limit"] or eligible<max(20,int(.7*len(selected))) or stats["stored_new"]<.9*eligible:
        raise SystemExit("Coverage/access gate failed; partial artifact preserved.")
if __name__=="__main__":
    main()

