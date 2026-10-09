"""Research-only DIPSAUS recovery pre-screen. No live quotes or trade signals."""
import gzip, json, math, os, subprocess, tempfile
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path("reports")
ROOT.mkdir(exist_ok=True)
SOURCE=ROOT/"ohlcv.jsonl.gz"

def restore():
    if SOURCE.exists():
        return
    repo=os.environ.get("GITHUB_REPOSITORY","owner/private-state-repository")
    token=os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if not token:
        raise RuntimeError("Missing GitHub token for database restoration")
    env=dict(os.environ,GH_TOKEN=token)
    api=subprocess.run(["gh","api",f"repos/{repo}/actions/artifacts?per_page=100"],env=env,capture_output=True,text=True,check=True)
    artifacts=json.loads(api.stdout)["artifacts"]
    candidates=[a for a in artifacts if a["name"]=="ohlcv-incremental" and not a["expired"]]
    if not candidates:
        raise RuntimeError("No cumulative database artifact found")
    errors=[]
    for a in candidates:
        try:
            with tempfile.TemporaryDirectory() as temp:
                run=a.get("workflow_run") or {}
                if not run.get("id"):
                    continue
                p=subprocess.run(["gh","run","download",str(run["id"]),"-R",repo,"-n",a["name"],"-D",temp],env=env,capture_output=True,text=True,timeout=120)
                if p.returncode:
                    raise RuntimeError(p.stderr[:250])
                matches=list(Path(temp).rglob("ohlcv.jsonl.gz"))
                if not matches:
                    raise RuntimeError("No database in artifact")
                SOURCE.write_bytes(matches[0].read_bytes())
                return
        except Exception as exc:
            errors.append(str(exc))
    raise RuntimeError("Cannot restore database: "+"; ".join(errors[:3]))

def assess(symbol,bars):
    clean=[]
    for bar in bars:
        if not isinstance(bar,list) or len(bar)<6:
            continue
        day,o,h,l,c,v=bar[:6]
        if all(isinstance(x,(int,float)) and math.isfinite(x) for x in (o,h,l,c,v)) and l>0 and l<=min(o,c)<=max(o,c)<=h and v>=0:
            clean.append((day,float(o),float(h),float(l),float(c),float(v)))
    clean.sort(key=lambda r:r[0])
    if len(clean)<150:
        return None,"insufficient_history"
    last=clean[-1]
    highs=[x[2] for x in clean]
    closes=[x[4] for x in clean]
    lows=[x[3] for x in clean]
    volumes=[x[5] for x in clean]
    peak=max(highs[-126:])
    drawdown=last[4]/peak-1
    if drawdown>-.20:
        return None,"not_sufficiently_sold_off"
    if last[4]<5 or sum(volumes[-20:])/20*last[4]<1_000_000:
        return None,"liquidity_or_price"
    recent_low=min(lows[-20:])
    low_prior=min(lows[-20:-5])
    ma5=sum(closes[-5:])/5
    ma20=sum(closes[-20:])/20
    prior_ma5=sum(closes[-10:-5])/5
    signals={
        "higher_recent_low":min(lows[-5:])>low_prior,
        "above_5d_average":last[4]>ma5,
        "5d_average_rising":ma5>prior_ma5,
        "above_20d_average":last[4]>ma20,
        "up_from_20d_low_3pct":last[4]>=recent_low*1.03,
    }
    count=sum(signals.values())
    if count<2:
        return None,"no_early_bottom_confirmation"
    return {
        "symbol":symbol,"last_bar_date":last[0],"last_unadjusted_close":round(last[4],4),
        "drawdown_from_126d_high_pct":round(drawdown*100,2),
        "average_20d_dollar_volume":round(sum(volumes[-20:])/20*last[4]),
        "early_signals":signals,"signal_count":count,
        "research_only":True,"trade_ready":False,
    },None

def main():
    restore()
    records=[]
    with gzip.open(SOURCE,"rt",encoding="utf-8") as stream:
        for line in stream:
            if line.strip():
                records.append(json.loads(line))
    if not records:
        raise RuntimeError("Database empty")
    output=[]
    excluded={}
    latest={}
    for entry in records:
        result,reason=assess(entry["symbol"],entry["bars"])
        if result:
            output.append(result)
            latest[result["last_bar_date"]]=latest.get(result["last_bar_date"],0)+1
        else:
            excluded[reason]=excluded.get(reason,0)+1
    output.sort(key=lambda x:(-x["signal_count"],x["drawdown_from_126d_high_pct"],x["symbol"]))
    report={"generated_utc":datetime.now(timezone.utc).isoformat(),
      "stored_symbols_examined":len(records),"passed_technical_prescreen":len(output),
      "excluded":excluded,"last_bar_dates_of_passed":latest,
      "full_us_universe_scanned":False,"live_quotes_verified":False,"trade_ready":False,
      "warning":"Unadjusted daily Yahoo OHLCV. Technical research only: no corporate-action adjustment, fundamentals, news, real-time price, true resistance, R/R, EUR money gate or portfolio fit."}
    (ROOT/"recovery_prescreen.json").write_text(json.dumps({"audit":report,"candidates":output},indent=2))
    print(json.dumps(report,indent=2))
    print("Top research candidates:",", ".join(x["symbol"] for x in output[:20]))
if __name__=="__main__":
    main()

