"""R01–R10 lifecycle regressions with a synthetic clock and no external delivery."""
import json
import tempfile
import unittest
from contextlib import chdir
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

import manual_recovery_trigger_watch as watch
from private_notifications import notify
from test_eu_research_freshness import Store
from test_us_recovery_chain import PRICES, START, snapshot
from us_recovery_continuity import EVIDENCE_MAX_AGE

NOW = datetime(2026, 11, 24, 15, 12, 59, tzinfo=timezone.utc)
DAY = NOW.date().isoformat()
SOURCE = 'Yahoo Finance chart 1m'


class TestClock(datetime):
    current = NOW

    @classmethod
    def now(cls, tz=None):
        return cls.current


def automatic(symbol='VIK', *, early=True, validated=NOW, **changes):
    minute = int(validated.timestamp()) // 60 * 60 - 60
    stamp = datetime.fromtimestamp(minute, timezone.utc).isoformat()
    shape = {'recovery_low': 100, 'higher_low': 101, 'path_efficiency': .6, 'reclaim_observed': False,
             'early_recovery_observed': True, 'quality': not early}
    qualification = (validated - timedelta(minutes=10)).isoformat()
    row = {'symbol': symbol, 'market': 'US', 'watch_type': 'AUTO-US-DISCOVERY',
           'status': 'EARLY-RECOVERY-WATCH' if early else 'DEGIRO-VERIFY-NOW',
           'phone_notification_eligible': True, 'provider_freshness_pass': True, 'structure_available': True,
           'early_turn_observed': True, 'prealert_trigger_observed': not early, 'intraday_hold_confirmed': not early,
           'hold_observed': not early, 'provider_source': SOURCE, 'provider_quote_utc': stamp,
           'provider_quote': 102, 'completed_minute_bar': {'ts': minute, 'close': 102},
           'latest_completed_minute_missing': False, 'day_low': 100,
           'setup_id': 'current', 'setup_floor': 100, 'setup_floor_ts': minute - 660,
           'alert_qualification_utc': [qualification],
           'route_evidence': {'fast': {'qualification_utc': qualification, 'early': True,
                                       'confirmed': not early, 'structure': shape}}}
    return {**row, **changes}


class NotificationRepairs(unittest.TestCase):
    def setUp(self):
        TestClock.current = NOW
        self.sent = []
        self.state = {'signals': {}}
        self.store = Store()
        self.enterContext(patch('private_notifications.datetime', TestClock))

    def send(self, *rows):
        notify(self.store, self.state, rows, [], sender=lambda symbol, body: self.sent.append((symbol, body)))

    def expire_during_reservation(self):
        self.store.after_save = lambda: setattr(TestClock, 'current', NOW + timedelta(seconds=2))

    def test_R01_expired_early_retries_with_a_new_validation(self):
        self.expire_during_reservation()
        self.send(automatic())
        self.assertFalse(self.sent)
        self.assertEqual(self.state['signals'][f'US-EARLY|VIK|{DAY}']['delivery'], 'expired_before_send')
        self.store.after_save = None
        self.send(automatic(validated=TestClock.current))
        self.assertEqual([symbol for symbol, _ in self.sent], ['VIK'])

    def test_R02_expired_confirmed_retries_with_a_new_validation(self):
        self.expire_during_reservation()
        self.send(automatic(early=False))
        self.assertFalse(self.sent)
        self.assertEqual(self.state['signals']['ENTRY|US|VIK|PHASE']['delivery'], 'expired_before_send')
        self.store.after_save = None
        self.send(automatic(early=False, validated=TestClock.current))
        self.assertEqual([symbol for symbol, _ in self.sent], ['VIK'])

    def test_expired_promotion_keeps_the_last_confirmed_delivery(self):
        key = 'ENTRY|US|VIK|PHASE'
        self.send(automatic(early=False))
        previous = dict(self.state['signals'][key])
        self.expire_during_reservation()
        self.send(automatic(early=False, breakout_observed=True))
        self.assertEqual(self.state['signals'][key], previous)
        self.assertEqual(len(self.sent), 1)
        expired = [item for key, item in self.state['signals'].items() if '|EXPIRED|' in key]
        self.assertEqual(expired[0]['delivery'], 'expired_before_send')
        self.store.after_save = None
        self.send(automatic(early=False, breakout_observed=True, validated=TestClock.current))
        self.assertEqual(len(self.sent), 2)
        self.assertEqual(self.state['signals'][key]['confirmed_attempts_today'], 2)

    def test_legacy_expired_promotion_retains_previous_delivered_rank(self):
        key = 'ENTRY|US|VIK|PHASE'
        self.state['signals'] = {key: {'delivery': 'expired_before_send', 'phase': 'BREAKOUT-HOLD-RETEST'},
                                 'ENTRY|US|VIK|HISTORY|legacy': {'delivery': 'sent', 'day': DAY,
                                                                   'phase': 'CURRENT-RECOVERY-CONFIRMED'}}
        self.send(automatic(early=False))
        self.assertFalse(self.sent)
        self.send(automatic(early=False, breakout_observed=True))
        self.assertEqual(len(self.sent), 1)

    def test_R03_uncertain_early_send_never_repeats_or_promotes_that_day(self):
        with self.assertRaises(TimeoutError):
            notify(self.store, self.state, [automatic()], [], sender=lambda *_: self.fail_uncertain())
        self.assertEqual(self.state['signals'][f'US-EARLY|VIK|{DAY}']['delivery'], 'uncertain')
        self.send(automatic(), automatic(early=False))
        self.assertEqual(len(self.sent), 1)

    def fail_uncertain(self):
        self.sent.append(('VIK', 'unknown delivery'))
        raise TimeoutError('simulated ambiguous transport')

    def test_ambiguous_server_error_remains_charged_and_blocks_resend(self):
        from urllib.error import HTTPError

        def fail(*args):
            raise HTTPError('synthetic', 503, 'ambiguous', {}, None)

        with self.assertRaisesRegex(RuntimeError, 'NOTIFICATION_DELIVERY_UNCERTAIN'):
            notify(self.store, self.state, [automatic()], [], sender=fail)
        self.assertEqual(self.state['signals'][f'US-EARLY|VIK|{DAY}']['delivery'], 'uncertain')
        self.send(automatic(), automatic(early=False))
        self.assertFalse(self.sent)

    def test_R04_missing_invalid_automatic_qualification_or_source_cannot_send(self):
        for changes in ({'alert_qualification_utc': None}, {'alert_qualification_utc': []},
                        {'alert_qualification_utc': {'malformed': NOW.isoformat()}},
                        {'provider_source': None}, {'provider_source': 'unrecognized'},
                        {'provider_quote_utc': None}, {'completed_minute_bar': None}):
            with self.subTest(changes=changes):
                self.state = {'signals': {}}
                self.sent = []
                self.send(automatic(**changes))
                self.assertEqual(self.sent, [])
                self.assertEqual(self.state['signals'], {})

    def test_R05_qualification_that_expires_during_reservation_blocks_send(self):
        clock_at_start = NOW - timedelta(seconds=20)
        TestClock.current = clock_at_start
        self.store.after_save = lambda: setattr(TestClock, 'current', clock_at_start + timedelta(seconds=2))
        valid = (clock_at_start - timedelta(seconds=EVIDENCE_MAX_AGE - 1)).isoformat()
        row = automatic(validated=clock_at_start, alert_qualification_utc=[valid])
        row['route_evidence']['fast']['qualification_utc'] = valid
        self.send(row)
        self.assertFalse(self.sent)
        self.assertEqual(self.state['signals'][f'US-EARLY|VIK|{DAY}']['delivery'], 'expired_before_send')

    def test_R06_definitely_unsent_records_do_not_use_daily_budget(self):
        self.state['signals'] = {f'US-EARLY|{symbol}|{DAY}': {'delivery': status, 'day': DAY}
                                 for symbol, status in [('AAA', 'expired_before_send'), ('BBB', 'rejected'), ('CCC', 'sent')]}
        self.send(automatic('VIK'), automatic('TSLA'), automatic('REZI'))
        self.assertEqual(len(self.sent), 2)

    def test_R07_manual_and_portfolio_watches_survive_automatic_rotation(self):
        symbols = [f'A{chr(65 + index // 26)}{chr(65 + index % 26)}' for index in range(38)] + ['VIK', 'ZZZ']
        routes = [{'symbol': symbol, 'phone_notification_eligible': True} for symbol in symbols]
        self.assertNotIn('VIK', {item['symbol'] for item in watch.automatic_watch_sample(routes, 0)})
        with tempfile.TemporaryDirectory() as directory, chdir(directory):
            Path('config').mkdir()
            watch.CONFIG.write_text(json.dumps({'candidates': {'VIK': {'market': 'US', 'invalidation_usd': 98}}}))
            Path('config/portfolio_reentry_watch.json').write_text(json.dumps({'candidates': {'ZZZ': {'market': 'US'}}}))
            watch.US_ROUTES.write_text(json.dumps({'rows': routes}))
            with patch.dict('os.environ', {'US_MONITOR_ROUND': '0'}), patch.object(
                    watch, 'fetch_minute_snapshot', side_effect=lambda symbol: snapshot(symbol, PRICES)) as fetch:
                watch.main()
            rows = {row['symbol']: row for row in json.loads(watch.OUT.read_text())['rows']}
        self.assertIn('VIK', rows)
        self.assertIn('ZZZ', rows)
        self.assertEqual(rows['VIK']['watch_type'], 'MANUAL-US-RECOVERY')
        self.assertIn('manual', rows['VIK']['route_evidence'])
        self.assertEqual(rows['ZZZ']['watch_type'], 'PORTFOLIO-REENTRY')
        self.assertEqual(sum(call.args == ('VIK',) for call in fetch.call_args_list), 1)
        self.assertEqual(sum(call.args == ('ZZZ',) for call in fetch.call_args_list), 1)

    def test_selected_overlap_shares_one_snapshot_and_keeps_separate_routes(self):
        auto = {'symbol': 'VIK', 'phone_notification_eligible': True, 'notification_lanes': ['fast'],
                'live_routes': {'fast': {'floor': 98, 'floor_ts': START, 'qualification_utc': NOW.isoformat()}}}
        manual = watch.manual_us_route('VIK', {'invalidation_usd': 99})
        with patch.object(watch, 'fetch_minute_snapshot', return_value=snapshot('VIK', PRICES)) as fetch:
            row = watch.watch_us(manual, {}, watch_type='MANUAL-US-RECOVERY', automatic=auto)
        fetch.assert_called_once_with('VIK')
        self.assertEqual(set(row['route_evidence']), {'manual', 'fast'})
        self.assertEqual(row['manual_watch_type'], 'MANUAL-US-RECOVERY')
        self.assertEqual(row['watch_type'], 'AUTO-US-DISCOVERY')

    def test_R09_stronger_early_recovery_is_selected_before_weak_rows(self):
        weak = [automatic(symbol) for symbol in ('AAA', 'BBB', 'CCC')]
        for row in weak:
            row['route_evidence']['fast']['structure'].update(higher_low=100.1, path_efficiency=.12)
        strong = automatic('VIK')
        strong['route_evidence']['fast']['structure'].update(higher_low=101.6, path_efficiency=.8)
        self.send(*weak, strong)
        self.assertEqual([symbol for symbol, _ in self.sent], ['VIK', 'AAA', 'BBB'])

    def test_R10_a_breached_bottom_invalidates_the_old_setup(self):
        item = {'symbol': 'TSLA', 'phone_notification_eligible': True,
                'notification_lanes': ['fast'], 'live_routes': {'fast': {'floor': 99, 'floor_ts': START,
                    'qualification_utc': NOW.isoformat()}}}
        with patch.object(watch, 'fetch_minute_snapshot', return_value=snapshot('TSLA', PRICES + [98, 98.2])):
            row = watch.watch_us(item, {})
        self.assertEqual(row['status'], 'SETUP-INVALIDATED')
        self.assertFalse(row['intraday_hold_confirmed'])
        self.assertFalse(row['prealert_trigger_observed'])
        self.assertEqual(row['route_evidence']['fast']['breach_ts'], START + len(PRICES) * 60)
        self.send(row)
        self.assertFalse(self.sent)
