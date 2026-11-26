"""Offline producer, private runner and notification regressions for US continuity."""
import copy
import json
import os
import tempfile
import unittest
from contextlib import chdir
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

import safe_runner
import us_momentum_recovery_discovery as fast_producer
from manual_recovery_trigger_watch import automatic_watch_sample, watch_us
from private_notifications import notify
from test_eu_research_freshness import Store
from test_us_recovery_chain import PRICES, SESSION_OPEN, START, fixture, snapshot
from us_auto_prealert_handoff import build_handoff
from us_live_trigger_routes import build_routes, persist_lane_breaches, route_rows
from us_yahoo_bars import minute_snapshot, require_current_daily_history

NOW = SESSION_OPEN + timedelta(minutes=12, seconds=39)


def fast(stamp=NOW, *, tickers=('VIK',), minute='VALID'):
    return {'generated_utc': stamp.isoformat(), 'candidates': [{
        'symbol': symbol, 'name': 'Synthetic Company', 'minute_data_status': minute,
        'day_change_pct': -.4, 'recent_drawdown_pct': -16, 'discovery_rank': rank,
        'intraday_structure': {'recovery_low': 99, 'recovery_low_ts': START,
                               'first_rebound_high': 104, 'early_recovery_observed': True},
    } for rank, symbol in enumerate(tickers, 1)]}


def deep(stamp=NOW, *, selected=True, disputed=False):
    candidate = {'symbol': 'VIK', 'last_bar_date': '2026-11-23', 'name': 'Synthetic Company',
                 'research_triage': {'bottom_signal_count': 4, 'weekly_higher_low': True,
                                     'space_to_first_overhead_pct': 4},
                 'identity_status': 'IDENTITY_MISMATCH' if disputed else 'NAME_CONSISTENT_UNVERIFIED',
                 'pivot_zones': [{'low_usd': 105, 'high_usd': 108}],
                 'research_dossier': {'historical_invalidation_reference_usd': 98,
                                      'company_event': {'event_risk_cleared': False}}}
    return {'finished_utc': stamp.isoformat(), 'batch_index': 0, 'requested_symbols': 1,
            'actual_symbols_screened': 1, 'sample_symbols': ['VIK'], 'completed_symbols': ['VIK'],
            'deep_dive_queue': [candidate] if selected else [], 'candidates': [candidate],
            'identity_shortlist': [{'symbol': 'VIK', 'identity_status': 'IDENTITY_MISMATCH'}] if disputed else [],
            'failures': {}}


def update(*, previous=None, fast_report=None, deep_reports=(), gate=None, now=NOW, **options):
    report = build_handoff(deep_reports, fast_report or {}, now=now)
    return build_routes(report, gate or {}, now=now, previous=previous, **options)


class ContinuityTests(unittest.TestCase):
    def test_vik_retains_rights_outside_fast_rotation_with_fresh_structure_on_red_day(self):
        seeded = update(fast_report=fast())
        later = NOW + timedelta(seconds=1)
        retained = update(previous=seeded, now=later)
        row = retained['rows'][0]
        self.assertEqual(row['lane_outcomes']['fast'], 'NOT_SCANNED')
        self.assertTrue(row['phone_notification_eligible'])
        self.assertEqual(row['live_routes']['fast']['qualification_utc'], NOW.isoformat())
        with patch('manual_recovery_trigger_watch.fetch_minute_snapshot', return_value=snapshot('VIK', PRICES[:-1] + [102])):
            entry = watch_us(row, {})
        self.assertEqual(entry['status'], 'EARLY-RECOVERY-WATCH')
        self.assertFalse(entry['trade_ready'])
        now_class = type('TestClock', (datetime,), {'now': staticmethod(lambda zone=None: later)})
        sent = []
        with patch('private_notifications.datetime', now_class):
            notify(Store(), {'signals': {}}, [entry], [], sender=lambda *item: sent.append(item))
        self.assertEqual([symbol for symbol, _ in sent], ['VIK'])

    def test_provider_error_does_not_erase_rights_and_stale_quote_cannot_send(self):
        seeded = update(fast_report=fast())
        later = NOW + timedelta(seconds=1)
        failed = update(previous=seeded, now=later, fast_failed=True)
        row = failed['rows'][0]
        self.assertEqual(row['lane_outcomes']['fast'], 'DATA_UNAVAILABLE')
        self.assertTrue(row['phone_notification_eligible'])
        self.assertEqual(row['live_routes']['fast']['qualification_utc'], NOW.isoformat())
        with patch('manual_recovery_trigger_watch.fetch_minute_snapshot', side_effect=ValueError('FAILED')):
            entry = watch_us(row, {})
        notify(Store(), {'signals': {}}, [entry], [], sender=lambda *_: self.fail('stale or failed quote alerted'))
        self.assertFalse(entry['provider_freshness_pass'])

    def test_qualified_deferred_and_rejected_are_independent_and_do_not_rearm(self):
        seeded = update(fast_report=fast(), deep_reports=[deep()])
        later = NOW + timedelta(minutes=3)
        failed_fast = {'generated_utc': later.isoformat(), 'outcomes': {'VIK': 'discovery_gate_rejected'}, 'candidates': []}
        continued = update(previous=seeded, now=later, fast_report=failed_fast, deep_reports=[deep(later, selected=False)])
        self.assertEqual(continued['scan_outcomes']['VIK'], {'fast': 'REJECTED', 'deep': 'QUALIFIED_DEFERRED'})
        row = continued['rows'][0]
        self.assertEqual(row['notification_lanes'], ['deep'])
        self.assertEqual(row['live_routes']['deep']['qualification_utc'], NOW.isoformat())
        later += timedelta(minutes=3)
        next_cycle = update(previous=continued, now=later, fast_failed=True)
        self.assertEqual(next_cycle['rows'][0]['notification_lanes'], ['deep'])
        self.assertTrue(next_cycle['lane_registry']['VIK']['fast']['qualification_retired'])
        self.assertEqual(next_cycle['lane_registry']['VIK']['fast']['qualification']['utc'], NOW.isoformat())

    def test_partial_deep_retry_that_reorders_queue_keeps_original_qualification(self):
        later = NOW + timedelta(minutes=1)
        result = update(deep_reports=[deep(), deep(later, selected=False)], now=later)
        self.assertEqual(result['scan_outcomes']['VIK']['deep'], 'QUALIFIED_DEFERRED')
        self.assertEqual(result['rows'][0]['live_routes']['deep']['qualification_utc'], NOW.isoformat())

    def test_expiration_and_explicit_revocation_survive_gate_changes_and_outages(self):
        fresh = update(fast_report=fast(), deep_reports=[deep()])
        later = NOW + timedelta(days=7, seconds=1)
        expired = update(previous=fresh, now=later, fast_failed=True, failed_batches={0})
        self.assertEqual(expired['scan_outcomes']['VIK'], {'fast': 'EXPIRED', 'deep': 'EXPIRED'})
        self.assertFalse(any(row['phone_notification_eligible'] for row in expired['rows']))
        later = NOW + timedelta(minutes=2)
        revoked = update(previous=fresh, now=later, gate={'auto_us_revoked': ['VIK']})
        self.assertEqual(revoked['scan_outcomes']['VIK'], {'fast': 'REVOKED', 'deep': 'REVOKED'})
        next_rows = route_rows(revoked['lane_registry'], {}, now=later + timedelta(seconds=1))
        self.assertFalse(next_rows[0]['phone_notification_eligible'])
        self.assertTrue(next_rows[0]['explicitly_revoked'])

    def test_identity_dispute_in_deep_route_blocks_current_fast_notification(self):
        data = update(fast_report=fast(), deep_reports=[deep(disputed=True)])
        row = data['rows'][0]
        self.assertTrue(row['identity_disputed'])
        self.assertFalse(row['phone_notification_eligible'])
        self.assertEqual(data['scan_outcomes']['VIK']['deep'], 'REVOKED')
        self.assertIn('fast', row['live_routes'])

    def test_tsla_actual_breach_persists_across_provider_outage_for_that_setup_only(self):
        routes = update(fast_report=fast(tickers=('TSLA',)))['rows']
        item = routes[0]
        payload = snapshot('TSLA', PRICES + [98, 98.2])
        with patch('manual_recovery_trigger_watch.fetch_minute_snapshot', return_value=payload):
            entry = watch_us(item, {})
        self.assertEqual(entry['status'], 'SETUP-INVALIDATED')
        memory = persist_lane_breaches(routes, [entry], {})
        self.assertEqual(memory['TSLA']['fast']['breach_ts'], START + len(PRICES) * 60)
        self.assertEqual(persist_lane_breaches(routes, [], memory), memory)
        changed_routes = copy.deepcopy(routes)
        changed_routes[0]['live_routes']['fast']['qualification_utc'] = (NOW + timedelta(minutes=3)).isoformat()
        self.assertEqual(persist_lane_breaches(changed_routes, [], memory), {})

    def test_old_proof_is_not_refreshed_by_new_report_time(self):
        stale = fast()
        stale['candidates'][0]['observed_utc'] = (NOW - timedelta(days=8)).isoformat()
        replayed = update(fast_report=stale)
        self.assertEqual(replayed['scan_outcomes']['VIK']['fast'], 'EXPIRED')
        self.assertFalse(replayed['rows'])


    def test_runner_rotation_to_private_store_to_live_validation_and_mock_sender(self):
        import manual_recovery_trigger_watch as watch_script
        state = {'signals': {}}
        us_store, alert_store, eu_store = Store(), Store(), Store()
        sent = []
        # The fixture is a regular trading session, independent of the test day.
        now_class = type('TestClock', (datetime,), {'now': staticmethod(lambda zone=None: NOW)})
        with tempfile.TemporaryDirectory() as directory, chdir(directory):
            Path('config').mkdir()
            for file, value in {
                'profit_exit_watch.json': {'positions': {}},
                'manual_recovery_triggers.json': {'candidates': {}},
                'notification_quality_gate.json': {'auto_us_notify_watchlist': [], 'auto_us_silent_follow': []},
            }.items():
                (Path('config') / file).write_text(json.dumps(value))
            sweeps = iter((fast(NOW - timedelta(minutes=5)), {'generated_utc': NOW.isoformat(),
                                                               'candidates': [], 'outcomes': {'OTHER': 'provider_error'}}))

            def run(script, **kwargs):
                if script == 'us_momentum_recovery_discovery.py':
                    Path(kwargs['US_FAST_REPORT']).write_text(json.dumps(next(sweeps)))
                elif script == 'us_recovery_pilot.py':
                    Path('reports/us_recovery_pilot.json').write_text(json.dumps({
                        'batch_index': kwargs['US_BATCH'], 'finished_utc': NOW.isoformat(), 'deep_dive_queue': []}))
                elif script == 'manual_recovery_trigger_watch.py':
                    watch_script.main()
                elif script == 'profit_exit_watch.py':
                    Path('reports/profit_exit_watch_report.json').write_text('{"rows": []}')

            def deliver(*args):
                notify(*args, sender=lambda *item: sent.append(item))

            with (patch.object(safe_runner, 'datetime', now_class), patch.object(safe_runner, 'run', side_effect=run),
                  patch.object(safe_runner, 'hydrate'), patch.object(safe_runner, 'sync_canonical_positions'),
                  patch.object(safe_runner, 'PrivateStore', side_effect={'us': us_store, 'prealert': alert_store, 'eu': eu_store}.get),
                  patch.object(safe_runner, 'notify', side_effect=deliver),
                  patch('private_notifications.datetime', now_class), patch.object(watch_script, 'datetime', now_class),
                  patch.object(watch_script, 'fetch_minute_snapshot', return_value=snapshot('VIK', PRICES[:-1] + [102])),
                  patch('company_event_watch.notify_events'), patch('silent_macro_context.update_silent_context'),
                  patch('dipsaus_fx_source.fetch_fx', return_value={'status': 'FX_UNAVAILABLE'}),
                  patch('sys.argv', ['safe_runner.py', 'prealert', '--live']),
                  patch.dict(os.environ, {'SCANNER_NOTIFICATIONS_ENABLED': 'true', 'GITHUB_ACTIONS': 'false'})):
                safe_runner.run_us_recovery(us_store, state)
                safe_runner.run_us_recovery(us_store, us_store.load())
                safe_runner.main()
            self.assertEqual(us_store.load()['us_routes']['scan_outcomes']['VIK']['fast'], 'NOT_SCANNED')
            self.assertEqual([symbol for symbol, _ in sent], ['VIK'])
            result = alert_store.load()
            self.assertEqual(result['latest_watch_reports']['entries']['automatic_monitor_outcomes']['VIK'], 'OBSERVED')
            self.assertEqual(next(record for key, record in result['signals'].items() if key.startswith('US-EARLY|'))['delivery'], 'sent')


class SourceAndSchedulerTests(unittest.TestCase):
    def test_rezi_missing_expected_last_minute_rejected_at_120_seconds(self):
        now = SESSION_OPEN + timedelta(minutes=13)
        payload, _ = fixture('REZI', PRICES, now=now)
        result = minute_snapshot(payload, 'REZI', now=now)
        self.assertEqual(result['bar_age_seconds'], 120)
        self.assertTrue(result['latest_completed_minute_missing'])
        self.assertFalse(result['fresh'])

    def test_stale_daily_chart_does_not_renew_a_qualification(self):
        require_current_daily_history([{'date': '2026-11-23'}], now=NOW)
        with self.assertRaisesRegex(ValueError, 'STALE_OR_FUTURE_DAILY_HISTORY'):
            require_current_daily_history([{'date': '2026-11-20'}], now=NOW)
        thanksgiving = datetime(2026, 11, 26, 17, tzinfo=timezone.utc)
        require_current_daily_history([{'date': '2026-11-25'}], now=thanksgiving)

    def test_fast_producer_uses_local_recovery_before_positive_daily_return(self):
        history = [{'date': '2026-11-23', 'high': 135, 'low': 99, 'close': 105, 'volume': 1_000_000}] * 35
        chart = snapshot('VIK', PRICES[:-1] + [102])
        clock = type('TestClock', (datetime,), {'now': staticmethod(lambda zone=None: NOW)})
        with (patch.object(fast_producer, 'datetime', clock), patch.object(fast_producer, 'chart_payload'),
              patch.object(fast_producer, 'daily_bars', return_value=history),
              patch.object(fast_producer, 'fetch_minute_snapshot', return_value=chart)):
            outcome, candidate = fast_producer.scan_candidate({'symbol': 'VIK', 'marketCap': 10_000_000_000})
        self.assertEqual(outcome, 'qualified')
        self.assertLess(candidate['day_change_pct'], 0)
        self.assertTrue(candidate['early_recovery_observed'])
        self.assertFalse(candidate['trade_ready'])

    def test_fast_producer_handoff_retains_more_than_thirty_and_rotates_polling(self):
        symbols = [f'A{i:02d}' for i in range(60)]
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'report.json'
            with patch.dict(os.environ, {'US_FAST_REPORT': str(output), 'US_FAST_SWEEP': '0'}), \
                    patch.object(fast_producer, 'universe', return_value=[{'symbol': symbol} for symbol in symbols]), \
                    patch.object(fast_producer, 'scan_candidate',
                                 side_effect=lambda issuer: ('qualified', dict(fast(tickers=[issuer['symbol']])['candidates'][0],
                                     early_recovery_observed=True, structure_quality_pass=False))):
                fast_producer.main()
            report = json.loads(output.read_text())
        self.assertEqual(len(report['candidates']), 60)
        self.assertEqual(report['candidates'][-1]['discovery_rank'], 60)
        routes = update(fast_report=report, now=datetime.now(timezone.utc))['rows']
        self.assertEqual(len(routes), 60)
        polled = {row['symbol'] for cycle in range(3) for row in automatic_watch_sample(routes, cycle)}
        self.assertEqual(polled, set(symbols))

    def test_failed_batch_retries_next_and_persists_unresolved_without_extra_attempts(self):
        with tempfile.TemporaryDirectory() as directory, chdir(directory):
            calls = []

            def run(script, **kwargs):
                if script == 'us_momentum_recovery_discovery.py':
                    Path(kwargs['US_FAST_REPORT']).write_text(json.dumps(fast()))
                    return
                batch = kwargs['US_BATCH']
                calls.append(batch)
                if batch == 4 or (batch == 0 and calls.count(0) == 1):
                    raise RuntimeError('SYNTHETIC_DOWN')
                Path('reports/us_recovery_pilot.json').write_text(json.dumps({**deep(), 'batch_index': batch}))

            store = Store()
            state = {'signals': {}, 'us_retry_batches': [4]}
            clock = type('TestClock', (datetime,), {'now': staticmethod(lambda zone=None: NOW)})
            with patch.object(safe_runner, 'run', side_effect=run), patch.object(safe_runner, 'datetime', clock):
                safe_runner.run_us_recovery(store, state)
            self.assertEqual(calls[:4], [4, 4, 0, 0])
            self.assertEqual(len(calls), 7)
            self.assertEqual(store.load()['us_retry_batches'], [4])
            self.assertIn(0, store.load()['us_last_completed_batches'])
            self.assertEqual(set(store.load()['us_routes']['rows'][0]['discovery_evidence']), {'fast', 'deep'})
