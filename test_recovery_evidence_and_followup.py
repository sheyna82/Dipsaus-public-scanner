"""Locked recovery evidence and bounded PRE-ALERT follow-up regressions."""
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from manual_recovery_trigger_watch import automatic_watch_sample, watch_us
from private_notifications import notify, phase
from recovery_price_evidence import breakout_stage, level_observations, resistance_room
from test_eu_research_freshness import Store
from test_us_notification_safety import us_row
from test_us_recovery_chain import PRICES, START, SESSION_OPEN, fixture, snapshot
from test_us_recovery_continuity import NOW, deep, fast, update
from us_live_trigger_routes import monitor_recovery
from us_yahoo_bars import minute_snapshot


class BreakoutEvidenceTests(unittest.TestCase):
    def test_cag_and_amgn_hold_cannot_come_from_an_unrelated_structure(self):
        for symbol, level, peak, price in [('CAG', 14.55, 14.68, 14.675), ('AMGN', 464.44, 467.07, 467.03)]:
            with self.subTest(symbol=symbol):
                row = {'market': 'US', 'symbol': symbol, 'provider_quote': price,
                       'intraday_hold_confirmed': True, 'hold_observed': True,
                       'breakout_observed': True, 'route_2_break_above': peak,
                       'completed_minute_bar': {'ts': START + 180, 'close': price},
                       'breakout_evidence': {'level': level,
                                             'breakout': {'ts': START + 60, 'close': price, 'low': level}}}
                self.assertEqual(phase(row), 'BREAKOUT-SEEN')
                self.assertEqual(phase({**row, 'breakout_evidence': {}}), 'CURRENT-RECOVERY-CONFIRMED')

    def test_retest_requires_separate_chronological_bars_at_the_same_level(self):
        bars = [{'ts': START + i * 60, 'close': close, 'low': low}
                for i, (close, low) in enumerate([(100, 99), (102, 100), (102, 101.5), (102, 101)])]
        proof = level_observations(bars, 101, START)
        self.assertEqual(breakout_stage(proof, bars[-1]['ts'], 102), 'retest')
        self.assertEqual(breakout_stage({**proof, 'retest': proof['hold']}, bars[-1]['ts'], 102), 'hold')
        self.assertEqual(breakout_stage({**proof, 'retest': {**proof['retest'], 'low': 101.5}},
                                        bars[-1]['ts'], 102), 'hold')
        self.assertFalse(level_observations(bars[:2] + bars[3:], 101, START))
        self.assertFalse(level_observations(bars, 101, START + 60))
        self.assertFalse(level_observations(bars + [{'ts': START + 240, 'close': 100, 'low': 100}], 101, START))

    def test_cag_message_uses_the_observed_breakout_level_for_the_distance(self):
        row = us_row(observed_at=NOW, symbol='CAG', provider_quote=14.675, route_2_break_above=14.68)
        last = row['completed_minute_bar']['ts']
        row['completed_minute_bar']['close'] = 14.675
        row['breakout_evidence'] = {'level': 14.55, 'breakout': {'ts': last - 60, 'close': 14.67, 'low': 14.55}}
        sent, clock = [], type('TestClock', (datetime,), {'now': staticmethod(lambda tz=None: NOW)})
        with patch('private_notifications.datetime', clock):
            notify(Store(), {'signals': {}}, [row], [], sender=lambda *message: sent.append(message))
        self.assertEqual(len(sent), 1)
        self.assertTrue(sent[0][1].startswith('CAG BREAKOUT-SEEN'))
        self.assertIn('Uitbraakafstand: 0.86%', sent[0][1])

    def test_wmt_monitor_can_confirm_a_real_retest_but_not_across_a_gap(self):
        row = {'symbol': 'WMT', 'phone_notification_eligible': True, 'notification_lanes': ['fast'],
               'live_routes': {'fast': {'floor': 99.9, 'floor_ts': START, 'level': 101.5,
                                        'level_observed_utc': (SESSION_OPEN + timedelta(minutes=3)).isoformat(),
                                        'qualification_utc': SESSION_OPEN.isoformat()}}}
        payload, now = fixture('WMT', PRICES + [103.5])
        quote = payload['chart']['result'][0]['indicators']['quote'][0]
        quote['low'][-1] = 101.5
        watch = monitor_recovery(row, minute_snapshot(payload, 'WMT', now=now))
        self.assertEqual(phase(watch), 'BREAKOUT-HOLD-RETEST')
        self.assertEqual(watch['route_2_break_above'], 101.5)
        replay_with_gap = snapshot('WMT', PRICES + [103.5], blanks=(10,))
        self.assertEqual(phase(monitor_recovery(row, replay_with_gap)), 'BOTTOM-RECOVERY')

    def test_cag_passed_first_historical_resistance_never_uses_next_zone(self):
        result = resistance_room(14.47, 15.08, price_basis='PROVIDER_COMPLETED_MINUTE')
        self.assertEqual((result['status'], result['remaining_pct']), ('PASSED', None))
        self.assertEqual(resistance_room(14.47, None, price_basis='PROVIDER_COMPLETED_MINUTE')['status'], 'UNAVAILABLE')
        self.assertAlmostEqual(resistance_room(105, 100, price_basis='DEGIRO_ASK')['remaining_pct'], 5)


class FollowUpTests(unittest.TestCase):
    def deferred_rezi(self):
        prior = NOW - timedelta(minutes=10)
        report = deep(prior)
        candidate = report['candidates'][0]
        candidate.update(symbol='REZI', identity_status='IDENTITY_UNVERIFIED')
        candidate['research_triage'].update(bottom_signal_count=2, early_turn=True, first_overhead_reference_usd=102)
        report.update(sample_symbols=['REZI'], completed_symbols=['REZI'])
        rejected = {'generated_utc': prior.isoformat(),
                    'outcomes': {'REZI': 'outside_recovery_or_liquidity_gate'}}
        return update(fast_report=rejected, deep_reports=[report])['rows'][0]

    def pending_fast(self, symbol, *, trough=99, gate=None, rejected_before=True):
        findings = fast(NOW - timedelta(minutes=10), tickers=[symbol])
        findings['candidates'][0].update(recent_20d_trough_usd=trough, last_bar_date='2026-11-23')
        seed = update(fast_report=findings)
        if not rejected_before:
            return seed['rows'][0]
        rejection = {'generated_utc': (NOW - timedelta(minutes=5)).isoformat(),
                     'outcomes': {symbol: 'discovery_gate_rejected'}}
        return update(previous=seed, fast_report=rejection, gate=gate)['rows'][0]

    def test_rezi_requalifies_from_deep_discovery_as_research_only(self):
        route = self.deferred_rezi()
        self.assertFalse(route['phone_notification_eligible'])
        self.assertEqual(route['follow_reasons'], {'deep': 'DEEP_EARLY_TURN'})
        self.assertEqual(automatic_watch_sample([route], 0), [route])
        sent, state = [], {'signals': {}}
        clock = type('TestClock', (datetime,), {'now': staticmethod(lambda tz=None: NOW)})
        with patch('manual_recovery_trigger_watch.fetch_minute_snapshot', return_value=snapshot('REZI', PRICES)):
            row = watch_us(route, {})
        self.assertTrue(row['phone_notification_eligible'])
        self.assertEqual(row['requalified_lanes'], ['deep'])
        self.assertEqual(row['status'], 'EARLY-RECOVERY-WATCH')
        self.assertFalse(row['prealert_trigger_observed'])
        self.assertFalse(row['trade_ready'])
        self.assertEqual(row['resistance_room']['status'], 'PASSED')
        with patch('private_notifications.datetime', clock):
            notify(Store(), state, [row, row], [], sender=lambda *message: sent.append(message))
        self.assertEqual(len(sent), 1)
        self.assertIn('ONDERZOEK', sent[0][1])
        self.assertIn('is gepasseerd', sent[0][1])

    def test_tsla_can_requalify_after_temporary_rejection_with_a_new_completed_minute(self):
        route = self.pending_fast('TSLA')
        self.assertFalse(route['phone_notification_eligible'])
        row = monitor_recovery(route, snapshot('TSLA', PRICES[:-1] + [102]))
        self.assertEqual(row['requalified_lanes'], ['fast'])
        self.assertEqual(row['status'], 'EARLY-RECOVERY-WATCH')
        self.assertFalse(row['intraday_hold_confirmed'])
        newer_route = {**route, 'live_routes': {'fast': {**route['live_routes']['fast'],
                                                        'recheck_after_utc': NOW.isoformat()}}}
        same_minute = monitor_recovery(newer_route, snapshot('TSLA', PRICES))
        self.assertFalse(same_minute['phone_notification_eligible'])
        too_extended = monitor_recovery(self.pending_fast('TSLA', trough=70), snapshot('TSLA', PRICES))
        self.assertFalse(too_extended['phone_notification_eligible'])

    def test_wmt_recheck_obeys_silence_revocation_age_and_source(self):
        wmt = snapshot('WMT', PRICES)
        silent = self.pending_fast('WMT', gate={'auto_us_silent_follow': ['WMT']})
        revoked = self.pending_fast('WMT', gate={'auto_us_revoked': ['WMT']})
        candidate = self.pending_fast('WMT')
        for route, quote in [(silent, wmt), (revoked, wmt),
                             (candidate, {**wmt, 'source': 'unknown'}),
                             (candidate, {**wmt, 'latest_completed_minute_missing': True})]:
            with self.subTest(route=route['status'], source=quote['source']):
                self.assertFalse(monitor_recovery(route, quote)['phone_notification_eligible'])
        old_route = {**candidate, 'live_routes': {'fast': {**candidate['live_routes']['fast'],
                           'watch_evidence_utc': (NOW - timedelta(days=8)).isoformat()}}}
        self.assertFalse(monitor_recovery(old_route, wmt)['phone_notification_eligible'])
