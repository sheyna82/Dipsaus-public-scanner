#!/usr/bin/env python3
import json
from datetime import datetime, timezone
from pathlib import Path
import yfinance as yf
from profit_map_validation import zone as profit_zone, assess as assess_profit_map

CFG=Path('config/profit_exit_watch.json')
OUT=Path('reports/profit_exit_watch_report.json')
MAX_AGE=120
cfg=json.loads(CFG.read_text())
now=datetime.now(timezone.utc)
rows=[]
for symbol,item in cfg.get('positions',{}).items():
    if item.get('status') == 'CLOSED-SWING':
        rows.append({'symbol':symbol,'status':'CLOSED-SWING','profit_alert':False,'automatic_sell':False})
        continue
    provider_symbol=item.get('provider_symbol',symbol)
    provider_currency=item.get('provider_currency',item.get('currency',item.get('broker_currency')))
    try:
        h=yf.Ticker(provider_symbol).history(period='5d',interval='1m',prepost=False)
        if h.empty:
            rows.append({'symbol':symbol,'status':'DATA-BLOCKED','profit_alert':False}); continue
        idx=h.index[-1]
        if getattr(idx,'tzinfo',None) is None: idx=idx.tz_localize('UTC')
        ts=idx.tz_convert('UTC').to_pydatetime(); age=(now-ts).total_seconds(); fresh=-30<=age<=MAX_AGE
        price=float(h['Close'].iloc[-1])
        reason=None; severity=None
        profit_map=item.get('profit_map') or {}
        zone=profit_zone(item, provider_currency, 'first_friction', 'first_decision_zone')
        if zone and price>=zone[0]: reason='FIRST-DECISION-ZONE'; severity='DECISION'
        meaningful=profit_zone(item, provider_currency, 'first_meaningful_resistance')
        if meaningful and price>=meaningful[0]: reason='MEANINGFUL-RESISTANCE'; severity='PARTIAL-PROFIT-CANDIDATE'
        friction=profit_zone(item, provider_currency, 'first_friction')
        suffix=str(provider_currency or '').lower()
        warning=item.get('warning_below_'+suffix) if suffix in ('eur','usd') else None
        giveback=item.get('material_giveback_'+suffix) if suffix in ('eur','usd') else None
        if friction:
            today=h[h.index.date==h.index[-1].date()]
            recent=today.tail(90) if not today.empty else h.tail(90)
            recent_high=float(recent['High'].max()) if not recent.empty else price
            tested=recent_high>=friction[0]
            if tested and giveback is not None and price<=giveback:
                reason='MATERIAL-BREAKOUT-GIVEBACK'; severity='FULL-EXIT-REASSESS'
            elif tested and warning is not None and price<warning:
                reason='FIRST-FRICTION-REJECTION'; severity='PARTIAL-PROFIT-CANDIDATE'
        # FAST-CRASH OVERRIDE: separate from normal 1h/swing profit logic.
        # Purpose: catch abnormal rapid downside damage early without making ordinary 5m pullbacks noisy.
        fast_crash=False; fast_metrics={}
        fc=item.get('fast_crash_override',False)
        if isinstance(fc,dict): fc_enabled=fc.get('enabled',True)
        else: fc_enabled=bool(fc)
        if fresh and fc_enabled:
            today=h[h.index.date==h.index[-1].date()]
            r=today.tail(20) if not today.empty else h.tail(20)
            if len(r)>=4:
                # 5m and 15m drawdown from a local high; also require downside acceleration / range expansion.
                p5=float(r['Close'].iloc[-6]) if len(r)>=6 else float(r['Close'].iloc[0])
                p15=float(r['Close'].iloc[-16]) if len(r)>=16 else float(r['Close'].iloc[0])
                drop5=(price/p5-1)*100
                drop15=(price/p15-1)*100
                local_high=float(r['High'].max())
                from_high=(price/local_high-1)*100
                ranges=(r['High']-r['Low'])
                last_range=float(ranges.iloc[-1])
                base_range=float(ranges.iloc[:-1].median()) if len(ranges)>1 else 0.0
                range_expansion=(last_range/base_range) if base_range>0 else 0.0
                red=int((r['Close'].tail(5)<r['Open'].tail(5)).sum())
                # Deliberately conjunctive: normal orderly retests stay quiet.
                fast_crash=bool((drop5<=-2.0 or drop15<=-3.0 or from_high<=-3.5) and (range_expansion>=1.5 or red>=4))
                fast_metrics={'drop_5m_pct':round(drop5,3),'drop_15m_pct':round(drop15,3),'from_20m_high_pct':round(from_high,3),'range_expansion':round(range_expansion,3),'red_bars_last5':red}
        # Provider-side exit pre-alert for cross-currency broker listings.
        # Never compare USD provider quotes directly with EUR Tradegate exit zones.
        # A configured USD reclaim only asks for a fresh broker check; execution still requires broker bid/ask/spread.
        exit_prealert=False; exit_prealert_level=None
        ew=item.get('exit_watch') or {}
        reclaim=ew.get('us_reclaim_context') or []
        if fresh and ew and provider_currency=='USD' and item.get('broker_currency')=='EUR' and reclaim:
            levels=sorted(float(x) for x in reclaim)
            # Highest reclaim level reached; useful as a broker-check escalation, never an automatic sell.
            reached=[x for x in levels if price>=x]
            if reached:
                exit_prealert=True; exit_prealert_level=max(reached)
                if not fast_crash:
                    reason='EXIT-REBOUND-BROKER-CHECK'; severity='DEGIRO-CHECK-NOW'
        if fast_crash:
            reason='FAST-CRASH-OVERRIDE'; severity='HIGH-URGENCY-DEGIRO-CHECK'
        alert=bool(fresh and reason)
        rows.append({'symbol':symbol,'shares':item.get('shares'),'provider_symbol':provider_symbol,'provider_currency':provider_currency,'broker_currency':item.get('broker_currency'),'provider_quote':price,'provider_quote_utc':ts.isoformat(),'fresh':fresh,'profit_alert':alert,'fast_crash':fast_crash,'fast_crash_metrics':fast_metrics,'exit_prealert':exit_prealert,'exit_prealert_level_usd':exit_prealert_level,'alert_reason':reason,'decision':severity,'status':'FAST-CRASH-DEGIRO-CHECK' if fast_crash else ('WINSTCHECK-NU' if alert else 'PROFIT-WATCH'),'automatic_sell':False})
    except Exception as e:
        rows.append({'symbol':symbol,'status':'DATA-BLOCKED','profit_alert':False,'error':type(e).__name__})
OUT.parent.mkdir(exist_ok=True)
for row in rows:
    item=cfg.get('positions',{}).get(row['symbol'],{})
    row['profit_map_validation']=assess_profit_map(item, row.get('provider_currency',item.get('currency')))
    row['dynamic_structure_monitoring']='NOT-IMPLEMENTED'
OUT.write_text(json.dumps({'generated_utc':now.isoformat(),'rows':rows},indent=2)+'\n')
print(OUT.read_text())

