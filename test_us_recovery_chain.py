"""Offline US source integrity and runner handoff using synthetic chart responses."""
import copy
import json
import os
import struct
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

import safe_runner
from private_notifications import notify
from us_auto_prealert_handoff import build_handoff
from us_execution_gate import evaluate_trade
from us_live_trigger_routes import build_routes, monitor_recovery
from us_yahoo_bars import FIELDS, daily_bars, minute_snapshot

ROOT = Path(__file__).resolve().parent
SESSION_OPEN = datetime(2026, 11, 24, 14, 30, tzinfo=timezone.utc)
SESSION_CLOSE = SESSION_OPEN + timedelta(hours=6, minutes=30)
START = int(SESSION_OPEN.timestamp())
PRICES = [100, 100.3, 101, 101.4, 101.9, 102.8, 103.5, 101.3, 101.1, 101.4, 101.6, 103.5]


def fixture(symbol, prices, *, blanks=(), irregular_last=None, now=None):
    stamps = [START + index * 60 for index in range(len(prices))]
    values = [[price, price + .04, price - .04, price, 100] for price in prices]
    for blank in blanks:
        values[blank] = [None] * 5
    now = now or SESSION_OPEN + timedelta(minutes=len(prices), seconds=39)
    reference = prices[-1] + .1234567
    meta = {'symbol': symbol, 'currency': 'USD', 'exchangeTimezoneName': 'America/New_York',
            'dataGranularity': '1m', 'currentTradingPeriod': {'regular': {'start': START, 'end': int(SESSION_CLOSE.timestamp())}},
            'regularMarketTime': int(now.timestamp()) - 1, 'regularMarketPrice': reference}
    if irregular_last is not None:
        quote = struct.unpack('!f', struct.pack('!f', reference))[0]
        stamps.append(meta['regularMarketTime'])
        values.append([quote] * 4 + [irregular_last])
    quote = {field: [row[index] for row in values] for index, field in enumerate(FIELDS)}
    return {'chart': {'result': [{'meta': meta, 'timestamp': stamps, 'indicators': {'quote': [quote]}}], 'error': None}}, now


def snapshot(symbol, prices, **kwargs):
    payload, now = fixture(symbol, prices, **kwargs)
    return minute_snapshot(payload, symbol, now=now)


class SourceIntegrityTests(unittest.TestCase):
    def test_float32_quote_update_removed_without_conflating_reference_and_close(self):
        parsed = snapshot('INTU', [100.0] * 119, irregular_last=0)
        self.assertTrue(parsed['terminal_quote_update_removed'])
        self.assertEqual(len(parsed['bars']), 119)
        self.assertEqual(parsed['latest_completed_bar']['close'], 100)
        self.assertGreater(parsed['reference']['price'], 100)
        self.assertEqual(parsed['bar_age_seconds'], 99)
        self.assertFalse(parsed['source_verified'])

    def test_off_grid_update_needs_time_price_ohlc_and_zero_volume_agreement(self):
        for field in ('price', 'time', 'ohlc', 'volume'):
            with self.subTest(field=field):
                payload, now = fixture('ORCL', PRICES, irregular_last=1 if field == 'volume' else 0)
                data = payload['chart']['result'][0]
                if field == 'price':
                    data['meta']['regularMarketPrice'] += .01
                if field == 'time':
                    data['meta']['regularMarketTime'] -= 1
                if field == 'ohlc':
                    data['indicators']['quote'][0]['high'][-1] += .01
                with self.assertRaisesRegex(ValueError, 'BAR_OUTSIDE_REGULAR_MINUTE_GRID'):
                    minute_snapshot(payload, 'ORCL', now=now)

    def test_aligned_flat_completed_minute_with_zero_volume_retained(self):
        payload, now = fixture('SNAP', PRICES)
        chart = payload['chart']['result'][0]
        chart['meta'].update(regularMarketTime=chart['timestamp'][-1], regularMarketPrice=PRICES[-1])
        for field in FIELDS:
            chart['indicators']['quote'][0][field][-1] = 0 if field == 'volume' else PRICES[-1]
        parsed = minute_snapshot(payload, 'SNAP', now=now)
        self.assertFalse(parsed['terminal_quote_update_removed'])
        self.assertEqual(len(parsed['bars']), 12)

    def test_aligned_metadata_update_at_session_close_has_no_bar(self):
        payload, _ = fixture('SNAP', [100] * 390, irregular_last=0,
                             now=SESSION_CLOSE + timedelta(seconds=1))
        parsed = minute_snapshot(payload, 'SNAP', now=SESSION_CLOSE + timedelta(seconds=1))
        self.assertTrue(parsed['terminal_quote_update_removed'])
        self.assertEqual(parsed['latest_completed_bar']['ts'], int(SESSION_CLOSE.timestamp()) - 60)

    def test_in_progress_minute_not_used_followed_by_live_update(self):
        now = SESSION_OPEN + timedelta(minutes=11, seconds=20)
        parsed = snapshot('CRDO', PRICES, now=now, irregular_last=0)
        self.assertEqual(len(parsed['bars']), 11)
        self.assertEqual(parsed['latest_completed_bar']['close'], PRICES[-2])

    def test_vicr_gaps_break_structure_and_empty_last_cannot_be_hidden(self):
        prices = [100] * 18
        parsed = snapshot('VICR', prices, blanks=range(4, 15), irregular_last=0)
        self.assertEqual((parsed['empty_completed_count'], len(parsed['bars'])), (11, 3))
        out = monitor_recovery({'symbol': 'VICR'}, parsed)
        self.assertFalse(out['structure_available'])
        with self.assertRaisesRegex(ValueError, 'EMPTY_LAST_COMPLETED_MINUTE_BAR'):
            snapshot('VICR', prices, blanks=(17,), irregular_last=0)

    def test_missing_timestamp_breaks_contiguity_without_reconstruction(self):
        payload, now = fixture('TEST', PRICES)
        chart = payload['chart']['result'][0]
        chart['timestamp'].pop(8)
        for values in chart['indicators']['quote'][0].values():
            values.pop(8)
        parsed = minute_snapshot(payload, 'TEST', now=now)
        self.assertEqual(len(parsed['bars']), 3)

    def test_partial_ohlc_misaligned_lengths_duplicates_session_and_identity_rejected(self):
        for mutation, reason in (
                (lambda c: c['timestamp'].__setitem__(1, c['timestamp'][0]), 'DUPLICATE_OR_NONCHRONOLOGICAL_BARS'),
                (lambda c: c['timestamp'].__setitem__(0, START - 60), 'BAR_OUTSIDE_REGULAR_MINUTE_GRID'),
                (lambda c: c['indicators']['quote'][0]['open'].__setitem__(0, None), 'PARTIAL_OR_INCONSISTENT_OHLCV'),
                (lambda c: c['indicators']['quote'][0]['high'].__setitem__(0, 1), 'PARTIAL_OR_INCONSISTENT_OHLCV'),
                (lambda c: c['indicators']['quote'][0]['volume'].pop(), 'OHLCV_LENGTH_MISMATCH'),
                (lambda c: c['meta'].update(symbol='OTHER'), 'CHART_SOURCE_IDENTITY_MISMATCH'),
                (lambda c: c['meta'].update(dataGranularity='5m'), 'CHART_SOURCE_IDENTITY_MISMATCH')):
            with self.subTest(reason=reason):
                payload, now = fixture('TEST', PRICES)
                mutation(payload['chart']['result'][0])
                with self.assertRaisesRegex(ValueError, reason):
                    minute_snapshot(payload, 'TEST', now=now)

    def test_daily_history_uses_source_identity_and_completed_sessions(self):
        payload, now = fixture('TEST', PRICES[:2])
        chart = payload['chart']['result'][0]
        chart['timestamp'] = [START - 86400, START]
        chart['meta']['dataGranularity'] = '1d'
        self.assertEqual(len(daily_bars(payload, 'TEST', now=now)), 1)
        self.assertEqual(len(daily_bars(payload, 'TEST', now=SESSION_CLOSE)), 2)


class RouteTests(unittest.TestCase):
    def deep(self, *, ready=True):
        return {'deep_dive_queue': [{'symbol': 'VIK', 'name': 'Example issuer', 'last_bar_date': '2026-11-23',
                'pivot_zones': [{'low_usd': 105, 'high_usd': 106}],
                'identity_status': 'NAME_CONSISTENT_UNVERIFIED',
                'research_triage': {'bottom_signal_count': 4, 'weekly_higher_low': ready,
                                    'space_to_first_overhead_pct': 4},
                'research_dossier': {'historical_invalidation_reference_usd': 98,
                    'company_event': {'earnings_status': 'FETCHED', 'earnings_dates': [{'date': '2026-11-25'}],
                                      'event_risk_cleared': False}}}]}

    def fast(self):
        return {'candidates': [{'symbol': 'VIK', 'recent_drawdown_pct': -15, 'day_change_pct': 2,
                                'intraday_structure': {'early_recovery_observed': True,
                                    'recovery_low': 99, 'recovery_low_ts': START, 'first_rebound_high': 104}}]}

    def test_two_lanes_share_one_ticker_without_losing_evidence(self):
        for deep_ready in (True, False):
            handoff = build_handoff([self.deep(ready=deep_ready)], self.fast(), now=SESSION_OPEN)
            self.assertEqual(len(handoff['rows']), 1)
            row = handoff['rows'][0]
            self.assertTrue(row['auto_promoted'])
            self.assertEqual(set(row['routes']), {'fast', 'deep'})
            live = build_routes(handoff, {}, now=SESSION_OPEN)['rows'][0]
            self.assertTrue(live['phone_notification_eligible'])
            self.assertEqual('deep' in live['live_routes'], deep_ready)
            self.assertEqual(live['live_routes']['fast']['level'], 104)

    def test_vik_early_and_confirmed_remain_distinct_and_keep_earnings_risk(self):
        handoff = build_handoff([self.deep()], self.fast(), now=SESSION_OPEN)
        route = build_routes(handoff, {}, now=SESSION_OPEN)['rows'][0]
        early = monitor_recovery(route, snapshot('VIK', PRICES[:-1] + [102]))
        confirmed = monitor_recovery(route, snapshot('VIK', PRICES))
        self.assertEqual((early['status'], confirmed['status']), ('EARLY-RECOVERY-WATCH', 'DEGIRO-VERIFY-NOW'))
        self.assertFalse(early['prealert_trigger_observed'])
        self.assertTrue(confirmed['intraday_hold_confirmed'])
        self.assertFalse(confirmed['company_event']['event_risk_cleared'])
        self.assertFalse(confirmed['trade_ready'])

    def test_tsla_old_setup_breach_then_new_structure_below_old_floor(self):
        item = {'symbol': 'TSLA', 'phone_notification_eligible': True,
                'live_routes': {'fast': {'floor': 100, 'floor_ts': START}}}
        previous = {'setup_floor': 100, 'setup_floor_ts': START}
        old = [price + 1 for price in PRICES]
        broken = monitor_recovery(item, snapshot('TSLA', old + [98, 98.5]), prior_alert=previous)
        self.assertEqual(broken['status'], 'SETUP-INVALIDATED')
        self.assertFalse(broken['prealert_trigger_observed'])
        previous['invalidated_at_ts'] = broken['previous_alert_invalidated_at_ts']
        new = [98 + (price - 100) * .5 for price in PRICES]
        rebuilt = monitor_recovery(item, snapshot('TSLA', old + new), prior_alert=previous)
        self.assertTrue(rebuilt['route_evidence']['fast']['old_setup_invalidated'])
        self.assertTrue(rebuilt['intraday_hold_confirmed'])
        self.assertLess(rebuilt['setup_floor'], 100)

    def test_rezi_old_minute_gates_structure_even_with_valid_price_path(self):
        old_now = SESSION_OPEN + timedelta(minutes=20)
        row = monitor_recovery({'symbol': 'REZI', 'phone_notification_eligible': True},
                               snapshot('REZI', PRICES, now=old_now))
        self.assertEqual(row['status'], 'STALE-PROVIDER')
        self.assertFalse(row['prealert_trigger_observed'])

    def test_new_us_setup_rearms_phase_once_original_breach_is_recorded(self):
        from test_eu_research_freshness import Store
        from zoneinfo import ZoneInfo
        now = datetime.now(timezone.utc)
        day = now.astimezone(ZoneInfo('America/New_York')).date().isoformat()
        key = 'ENTRY|US|TSLA|PHASE'
        state = {'signals': {key: {'phase': 'BREAKOUT-HOLD-RETEST', 'day': day, 'delivery': 'sent',
                                  'setup_id': 'old', 'confirmed_attempts_today': 1}}}
        floor_ts = int(now.timestamp()) - 60
        row = {'symbol': 'TSLA', 'market': 'US', 'watch_type': 'AUTO-US-DISCOVERY',
               'provider_source': 'Yahoo Finance chart 1m', 'provider_quote_utc': now.isoformat(),
               'provider_freshness_pass': True, 'phone_notification_eligible': True, 'structure_available': True,
               'early_turn_observed': True, 'hold_observed': True, 'intraday_hold_confirmed': True,
               'prealert_trigger_observed': True, 'setup_id': 'new', 'setup_floor_ts': floor_ts,
               'setup_floor': 98, 'previous_alert_invalidated_at_ts': floor_ts}
        sent, store = [], Store()
        notify(store, state, [row, row], [], sender=lambda *item: sent.append(item))
        self.assertEqual(len(sent), 1)
        self.assertEqual(state['signals'][key]['setup_id'], 'new')
        self.assertEqual(state['signals'][key]['confirmed_attempts_today'], 2)
        self.assertIn('ENTRY|US|TSLA|HISTORY|legacy', state['signals'])

    def test_runner_preserves_available_lane_even_when_other_lane_fails(self):
        for failing in ('deep', 'fast', 'malformed-deep', 'malformed-fast'):
            with self.subTest(failing=failing), tempfile.TemporaryDirectory() as folder:
                baseline = Path.cwd()
                try:
                    os.chdir(folder)
                    Path('config').mkdir()
                    saved = []

                    class Store:
                        def save(self, state):
                            saved.append(copy.deepcopy(state))

                    def run_script(script, **kwargs):
                        if script == 'us_momentum_recovery_discovery.py':
                            if failing == 'fast':
                                raise subprocess.TimeoutExpired(script, 1)
                            report = [] if failing == 'malformed-fast' else self.fast()
                            Path(kwargs['US_FAST_REPORT']).write_text(json.dumps(report))
                        elif script == 'us_recovery_pilot.py':
                            if failing == 'deep':
                                raise RuntimeError('SYNTHETIC_DEEP_FAILURE')
                            report = [] if failing == 'malformed-deep' else {
                                **self.deep(), 'batch_index': kwargs['US_BATCH']}
                            Path('reports/us_recovery_pilot.json').write_text(json.dumps(report))
                        else:
                            env = {**os.environ, **{key: str(value) for key, value in kwargs.items()}}
                            subprocess.run([sys.executable, ROOT / script], env=env, capture_output=True, check=True)

                    with patch.object(safe_runner, 'run', side_effect=run_script):
                        safe_runner.run_us_recovery(Store(), {'signals': {}})
                    rows = saved[-1]['us_routes']['rows']
                    self.assertEqual([row['symbol'] for row in rows], ['VIK'])
                    self.assertEqual(set(rows[0]['discovery_evidence']), {'fast' if failing.endswith('deep') else 'deep'})
                    self.assertEqual(len(saved[-1]['us_last_completed_batches']), 0 if failing.endswith('deep') else 7)
                finally:
                    os.chdir(baseline)


class FinancialCases(unittest.TestCase):
    def evaluate(self, symbol, **changes):
        from test_us_recovery import GateTests
        evidence = {**GateTests().evidence(), 'symbol': symbol, **changes}
        return evaluate_trade(evidence, now=datetime(2026, 9, 23, 18, 1, tzinfo=timezone.utc), max_risk_eur=150)

    def test_cag_distant_price_cannot_rescue_first_resistance(self):
        result = self.evaluate('CAG', first_meaningful_resistance_usd=104, realistic_target_usd=120)
        self.assertEqual(result['status'], 'MONEY_OR_RISK_BLOCKED')
        self.assertLess(result['net_profit_eur'], 150)

    def test_fico_expensive_shares_use_whole_share_budget_including_fees(self):
        result = self.evaluate('FICO', ask_usd=1950, bid_usd=1949, invalidation_usd=1900,
                               first_meaningful_resistance_usd=2150)
        self.assertEqual(result['whole_shares'], 1)
        self.assertEqual(result['notional_with_buy_fee_eur'], 1759)

    def test_rezi_stale_price_and_crossed_spread_cannot_confirm(self):
        self.assertEqual(self.evaluate('REZI', quote_utc='2026-09-23T17:55:00+00:00', bid_usd=96.5)['status'],
                         'STALE_OR_FUTURE_DATA')
        self.assertEqual(self.evaluate('REZI', bid_usd=96.5)['status'], 'STRUCTURE_BLOCKED')
        self.assertEqual(self.evaluate('REZI', bid_usd=101)['status'], 'STRUCTURE_BLOCKED')

    def test_vik_unverified_earnings_stay_blocked(self):
        result = self.evaluate('VIK', upcoming_material_events_verified=False)
        self.assertEqual(result['status'], 'REVIEW_BLOCKED')
        self.assertIn('upcoming_material_events_verified', result['unverified'])
