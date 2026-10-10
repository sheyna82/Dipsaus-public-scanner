import unittest
import contextlib
import io
import json
import os
import runpy
import sys
import tempfile
import types
from pathlib import Path
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch
import pandas as pd
from dynamic_profit_watch import structure, chart_map, evaluate

BASE=datetime(2026,10,8,8,tzinfo=timezone.utc)


def rows(lows, daily=False):
    return [{'time': (BASE+timedelta(days=i-7) if daily else BASE+timedelta(hours=i)).isoformat(),
             'low': x, 'high': x+2, 'open': x+.5, 'close': x+1, 'volume': 100} for i,x in enumerate(lows)]


class DynamicTests(unittest.TestCase):
    def setUp(self):
        self.h=rows([102,101,98,101,102,104,103,100,103,104,105,106])
        self.d=rows([90,91,92,93,94,95,96],daily=True)
        self.now=BASE+timedelta(hours=12,minutes=1)

    def test_confirmed_hourly_higher_low_and_ratchet(self):
        r,s=structure(self.h,self.d,107,self.now.isoformat(),self.now)
        self.assertEqual(s['reference']['price'],100)
        previous={'reference':{'price':101,'time':(BASE+timedelta(hours=6)).isoformat(),'confirmed_at':BASE.isoformat()}}
        r,s=structure(self.h,self.d,107,self.now.isoformat(),self.now,previous)
        self.assertEqual(s['reference']['price'],101)
        self.assertFalse(r['structure_alert'])

    def test_incomplete_confirmation_candle_is_ignored(self):
        now=BASE+timedelta(hours=9,minutes=30)
        r,s=structure(self.h,self.d,107,now.isoformat(),now)
        self.assertNotIn('reference',s)

    def test_confirmed_daily_reference_when_hourly_has_no_pivots(self):
        h=rows(list(range(110,122)))
        d=rows([102,101,98,101,102,104,103,100,103,104,105,106],daily=True)
        for i,r in enumerate(d):r['time']=(BASE-timedelta(days=12-i)).isoformat()
        r,s=structure(h,d,123,self.now.isoformat(),self.now)
        self.assertEqual(s['reference']['price'],100)
        self.assertEqual(s['reference']['timeframe'],'1d')
        self.assertFalse(r['structure_alert'])

    def test_normal_support_retest_stays_quiet(self):
        h=self.h[:-2]+rows([100,102])
        h[-2]['time']=self.h[-2]['time'];h[-1]['time']=self.h[-1]['time']
        prev={'reference':{'price':100,'time':BASE.isoformat(),'confirmed_at':BASE.isoformat()}}
        r,s=structure(h,self.d,102,self.now.isoformat(),self.now,prev)
        self.assertFalse(r['structure_alert'])
        self.assertGreaterEqual(r['same_zone_retests'],1)

    def deterioration(self):
        h=self.h[:-2]+rows([95,94]);h[-2]['time']=self.h[-2]['time'];h[-1]['time']=self.h[-1]['time']
        h[-1]['volume']=300
        prev={'reference':{'price':100,'time':(BASE-timedelta(days=1)).isoformat(),'confirmed_at':BASE.isoformat()}}
        return h,prev

    def test_two_completed_failures_and_acceleration_request_review(self):
        h,prev=self.deterioration()
        r,s=structure(h,self.d,95,self.now.isoformat(),self.now,prev)
        self.assertTrue(r['structure_alert']);self.assertFalse(r['automatic_sell'])
        self.assertEqual(s['reference']['price'],100)

    def test_stale_quote_never_alerts(self):
        h,prev=self.deterioration()
        r,s=structure(h,self.d,95,(self.now-timedelta(minutes=5)).isoformat(),self.now,prev)
        self.assertFalse(r['structure_alert'])

    def test_stale_history_never_alerts(self):
        h,prev=self.deterioration();now=self.now+timedelta(days=2)
        r,s=structure(h,self.d,95,now.isoformat(),now,prev)
        self.assertFalse(r['structure_alert']);self.assertEqual(r['status'],'STALE-STRUCTURE-DATA')

    def test_provider_error_preserves_reference_without_alert(self):
        ticker=MagicMock();ticker.history.side_effect=RuntimeError('provider private URL')
        prev={'identity':{'provider_symbol':'TEST','currency':'EUR','swing_id':None},'reference':{'price':100}}
        r,s,m=evaluate(ticker,{'provider_symbol':'TEST'},95,self.now.isoformat(),'EUR',self.now,prev)
        self.assertEqual(s['reference']['price'],100);self.assertFalse(r['structure_alert'])
        self.assertNotIn('private URL',str(r))

    def test_no_invented_zones_or_purchase_cost(self):
        m=chart_map(self.h,self.d,999,'EUR',{'shares':10},self.now)
        self.assertEqual(m['gross_profit_eur_at_zones'],{})
        self.assertIn('verified_average_cost',m['missing'])
        self.assertIsNone(m['zones']['further_recovery_zone'])

    def test_usd_requires_fresh_fx_for_euro_profit(self):
        m=chart_map(self.h,self.d,95,'USD',{'shares':10,'average_cost_usd':80},self.now,
                    {'eurusd':1.1,'time':(self.now-timedelta(hours=1)).isoformat()})
        self.assertIn('fresh_usd_eur_conversion',m['missing'])
        self.assertEqual(m['gross_profit_eur_at_zones'],{})

    def test_cache_reused_within_hour(self):
        ticker=MagicMock()
        prev={'identity':{'provider_symbol':'TEST','currency':'EUR','swing_id':None},
              'cache':{'fetched_utc':self.now.isoformat(),'hourly':self.h,'daily':self.d}}
        r,s,m=evaluate(ticker,{'provider_symbol':'TEST'},107,self.now.isoformat(),'EUR',self.now,prev)
        ticker.history.assert_not_called()

    def test_real_profit_script_produces_private_state_and_missing_cost(self):
        now=datetime.now(timezone.utc)
        h=rows([102,101,98,101,102,104,103,100,103,104,105,106])
        for i,r in enumerate(h):r['time']=(now-timedelta(hours=12-i,minutes=1)).isoformat()
        d=rows([90,91,92,93,94,95,96],daily=True)
        for i,r in enumerate(d):r['time']=(now-timedelta(days=7-i)).isoformat()
        def frame(records):
            return pd.DataFrame([{k.title():v for k,v in r.items() if k!='time'} for r in records],index=pd.DatetimeIndex([r['time'] for r in records]))
        q=frame([{'time':(now-timedelta(seconds=30)).isoformat(),'open':106,'high':108,'low':105,'close':107,'volume':100}])
        ticker=MagicMock();ticker.history.side_effect=lambda **kw: q if kw['interval']=='1m' else frame(h if kw['interval']=='1h' else d)
        script=Path(__file__).with_name('profit_exit_watch.py').resolve()
        cwd=Path.cwd()
        with tempfile.TemporaryDirectory() as tmp:
            try:
                os.chdir(tmp);Path('config').mkdir()
                Path('config/profit_exit_watch.json').write_text(json.dumps({'positions':{'TEST':{'currency':'EUR','shares':10,'dynamic_structure_protection':True,'profit_map_required':True}}}))
                with patch.dict(sys.modules,{'yfinance':types.SimpleNamespace(Ticker=lambda _:ticker)}),contextlib.redirect_stdout(io.StringIO()):runpy.run_path(str(script))
                result=json.loads(Path('reports/profit_exit_watch_report.json').read_text())
                self.assertEqual(result['dynamic_state']['TEST']['reference']['price'],100)
                row=result['rows'][0]
                self.assertFalse(row['profit_alert']);self.assertFalse(row['automatic_sell'])
                self.assertIn('verified_average_cost',row['chart_profit_map']['missing'])
            finally:os.chdir(cwd)

    def test_runner_persists_reference_separately_from_report(self):
        import safe_runner
        store=MagicMock();store.load.return_value={'signals':{},'profit_watch_state':{'TEST':{'reference':{'price':100}}}}
        cwd=Path.cwd()
        def scan(script):
            Path('reports').mkdir(exist_ok=True)
            if script=='profit_exit_watch.py':
                self.assertEqual(json.loads(Path('config/profit_watch_state.json').read_text())['TEST']['reference']['price'],100)
                Path('reports/profit_exit_watch_report.json').write_text(json.dumps({'rows':[],'dynamic_state':{'TEST':{'reference':{'price':101}}}}))
            else:Path('reports/manual_recovery_trigger_report.json').write_text('{"rows":[]}')
        with tempfile.TemporaryDirectory() as tmp:
            try:
                os.chdir(tmp)
                with patch('sys.argv',['safe_runner.py','prealert']),patch.object(safe_runner,'hydrate'),patch.object(safe_runner,'PrivateStore',return_value=store),patch.object(safe_runner,'run',side_effect=scan),patch.object(safe_runner,'notify') as notify,contextlib.redirect_stdout(io.StringIO()):safe_runner.main()
                saved=store.save.call_args.args[0]
                self.assertEqual(saved['profit_watch_state']['TEST']['reference']['price'],101)
                self.assertNotIn('dynamic_state',saved['latest_watch_reports']['exits'])
                notify.assert_not_called()
            finally:os.chdir(cwd)


if __name__=='__main__':unittest.main()
