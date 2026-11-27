"""Offline European report, private handoff and reservation regressions."""
import base64
import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch
from urllib.error import HTTPError

import safe_runner
from eu_entry_net import (DEGIRO_VERIFICATION, EARLY_RECOVERY, EVIDENCE_STATE_KEY,
                          FINANCIAL_ENTRY_CONFIRMED, REVIEWER_PIN_ENV, assess_report,
                          evaluate_entry, evidence_digest)
from private_notifications import notify_eu_research
from research_ed25519_verifier import DOMAIN
from research_net_attestation import FIELDS

NOW = datetime(2026, 11, 24, 15, 30, tzinfo=timezone.utc)
ROOT = Path(__file__).resolve().parent


class Store:
    def __init__(self, original=None, after_save=None):
        self.original = original or {'signals': {}}
        self.saved = []
        self.after_save = after_save

    def load(self):
        return copy.deepcopy(self.saved[-1] if self.saved else self.original)

    def require_exclusive_sender(self):
        pass

    def save(self, state):
        self.saved.append(copy.deepcopy(state))
        if self.after_save:
            self.after_save()


def report(age_minutes=1, *, now=NOW, symbols=('TEST.PA',)):
    return {'generated_utc': (now - timedelta(minutes=age_minutes)).isoformat(),
            'candidates': [{
                'symbol': symbol, 'currency': 'EUR', 'early_recovery_watch': True,
                'intraday_evidence': 'EARLY-STRUCTURE-OBSERVED',
                'last_15m_bar': (now - timedelta(minutes=12)).isoformat(),
                'provider_1m_quote_utc': (now - timedelta(minutes=15)).isoformat(),
                'broker_verify_now': True, 'broker_check_candidate': True,
                'trade_ready': False, 'order_placement_enabled': False,
                'provider_delayed_but_usable_for_attention': True,
                'early_recovery_score': 4, 'historical_flags': [],
            } for symbol in symbols]}


class SenderFixture:
    def send(self, data, *, state=None, holdings=(), now=NOW, store=None, evidence=None, pin=None, clock=None, positions=()):
        sent = []
        notify_eu_research(store or Store(), {'signals': {}} if state is None else state, data, set(holdings),
                           sender=lambda symbol, body: sent.append((symbol, body)),
                           evidence=evidence, reviewer_pin=pin, clock=clock or (lambda: now),
                           positions={} if positions == () else positions)
        return sent

class EUFreshnessTests(SenderFixture, unittest.TestCase):
    def test_delayed_provider_requests_broker_verification(self):
        self.assertIn(DEGIRO_VERIFICATION, self.send(report())[0][1])

    def test_invalid_future_expired_and_duplicate_report_never_notify(self):
        invalid = report()
        del invalid['generated_utc']
        for data in (invalid, report(26), report(-2), report(symbols=('TEST.PA', 'TEST.PA')), {'generated_utc': False}):
            with self.subTest(data=data):
                self.assertEqual(self.send(data), [])

    def test_expired_provider_is_early_if_structure_still_current(self):
        data = report()
        data['candidates'][0]['provider_1m_quote_utc'] = (NOW - timedelta(minutes=21)).isoformat()
        self.assertIn(EARLY_RECOVERY, self.send(data)[0][1])
        data['candidates'][0]['last_15m_bar'] = (NOW - timedelta(minutes=46)).isoformat()
        self.assertEqual(self.send(data), [])

    def test_phase_upgrade_dedupes_and_legacy_stage_counts_across_holding_change(self):
        state = {'signals': {}}
        data = report()
        row = data['candidates'][0]
        row['broker_verify_now'] = False
        self.assertIn(EARLY_RECOVERY, self.send(data, state=state)[0][1])
        row['broker_verify_now'] = True
        self.assertIn(DEGIRO_VERIFICATION, self.send(data, state=state, holdings=('TEST.PA',))[0][1])
        self.assertEqual(self.send(data, state=state), [])
        legacy = {'signals': {'EU-RESEARCH|TEST.PA|INSTAPCHECK': {'day': NOW.date().isoformat()}}}
        self.assertEqual(self.send(data, state=legacy, holdings=('TEST.PA',)), [])

    def test_caps_count_promotions_and_prioritize_watchlist_and_holding(self):
        state = {'signals': {}}
        symbols = ('KER.PA', 'OWN.PA', 'A.PA', 'B.PA', 'C.PA', 'D.PA', 'E.PA', 'F.PA')
        data = report(symbols=symbols)
        for row in data['candidates']:
            row['broker_verify_now'] = False
        sent = self.send(data, state=state, holdings=('OWN.PA',))
        self.assertEqual([symbol for symbol, _ in sent], ['KER.PA', 'OWN.PA', 'A.PA'])
        self.assertEqual(len(self.send(data, state=state)), 3)
        for row in data['candidates']:
            row['broker_verify_now'] = True
        self.assertEqual(len(self.send(data, state=state, holdings=('OWN.PA',))), 1)
        self.assertEqual(self.send(data, state=state, holdings=('OWN.PA',)), [])
        self.assertEqual(len(state['signals']), 7)
        self.assertEqual(sum(item['priority_lane'] for item in state['signals'].values()), 2)

    def test_held_score_and_bottom_quality_exceptions_are_preserved(self):
        data = report(symbols=('OWN.PA', 'NEW.PA', 'WEAK.PA'))
        data['candidates'][0].update(early_recovery_score=2, historical_flags=['BOTTOM-EVIDENCE-INSUFFICIENT'])
        data['candidates'][1].update(early_recovery_score=2)
        data['candidates'][2].update(historical_flags=['BOTTOM-EVIDENCE-INSUFFICIENT'])
        self.assertEqual([symbol for symbol, _ in self.send(data, holdings=('OWN.PA',))], ['OWN.PA'])

    def test_european_priority_and_active_holdings_reach_the_universe(self):
        from europe_ohlcv_pilot import recovery_universe
        groups = recovery_universe({'BROKER_ALIASED': {'provider_symbol': 'EXTRA.PA', 'shares': 5},
                                    'SOLD.DE': {'shares': 0}, 'US': {'shares': 10}})
        all_symbols = {symbol for symbols in groups.values() for symbol in symbols}
        self.assertTrue({'KER.PA', 'FER.MC', 'SU.PA', 'ANTO.L', 'EXTRA.PA'} <= all_symbols)
        self.assertNotIn('SOLD.DE', all_symbols)
        self.assertNotIn('US', all_symbols)

    def test_store_records_reserved_rejected_uncertain_and_sent(self):
        for error, status in ((None, 'sent'), (TimeoutError(), 'uncertain'),
                              (HTTPError('synthetic', 403, '', {}, None), 'rejected')):
            with self.subTest(status=status):
                state, store = {'signals': {}}, Store()
                body_at_send = []

                def sender(symbol, body):
                    body_at_send.append(next(iter(store.saved[-1]['signals'].values()))['delivery'])
                    if error:
                        raise error

                def send():
                    notify_eu_research(store, state, report(), set(), sender=sender, clock=lambda: NOW)

                if error:
                    with self.assertRaises((TimeoutError, RuntimeError)):
                        send()
                else:
                    send()
                self.assertEqual(body_at_send, ['reserved'])
                self.assertEqual(next(iter(store.saved[-1]['signals'].values()))['delivery'], status)
                self.assertEqual(self.send(report(), state=state), [])


class EUBrokerAndHandoffTests(SenderFixture, unittest.TestCase):
    # Use a real ephemeral Ed25519 key. It represents a reviewer only in this test.
    @classmethod
    def setUpClass(cls):
        import hashlib
        directory = tempfile.TemporaryDirectory()
        cls.addClassCleanup(directory.cleanup)
        cls.scratch = Path(directory.name)
        cls.key = cls.scratch / 'reviewer.pem'
        cls.pub = cls.scratch / 'reviewer.pub.pem'
        subprocess.run(['openssl', 'genpkey', '-algorithm', 'ED25519', '-out', cls.key], check=True)
        subprocess.run(['openssl', 'pkey', '-in', cls.key, '-pubout', '-out', cls.pub], check=True)
        cls.pin = hashlib.sha256(cls.pub.read_bytes()).hexdigest()

    def sign(self, payload):
        message = self.scratch / 'message'
        message.write_bytes(DOMAIN + bytes.fromhex(evidence_digest(payload)))
        signature = subprocess.check_output(['openssl', 'pkeyutl', '-sign', '-inkey', self.key,
                                            '-rawin', '-in', message])
        return {'payload': payload, 'public_key_pem': self.pub.read_text(),
                'signature_b64': base64.b64encode(signature).decode()}

    def inputs(self, *, now=NOW, bid=99.9, target=105, invalidation=98.5,
               buy=10, sell=10, slip_buy=0, slip_sell=0, symbol='TEST.PA', positions=None, capacity=None):
        from recovery_portfolio_capacity import holdings_digest
        positions = positions if positions is not None else {}
        stamp = now.isoformat()
        values = {'broker_ask': 100, 'broker_bid': bid, 'target': target, 'invalidation': invalidation,
                  'buy_fee_eur': buy, 'sell_fee_eur': sell, 'buy_slippage_per_share': slip_buy,
                  'sell_slippage_per_share': slip_sell, 'fx_eur_per_unit': 1, 'fx_buy_fee_rate': 0,
                  'fx_sell_fee_rate': 0, 'broker_quote_verified': True, 'levels_verified': True,
                  'fees_verified': True, 'fx_verified': True, 'quote_freshness_verified': True}
        identity = {'symbol': symbol, 'isin': 'FR0000121485', 'operating_mic': 'XPAR', 'currency': 'EUR'}
        attestations = {group: {'source_id': 'DEGIRO' if group == 'broker_quote' else 'INDEPENDENT_REVIEW',
                                'observed_utc': stamp, 'verified': True,
                                'fields': {key: values[key] for key in keys}} for group, keys in FIELDS.items()}
        return {'independently_reviewed': True, 'instrument': {**identity, 'identity_verified': True},
                'quote': {**identity, 'source': 'DEGIRO', 'observed_utc': stamp, 'market_utc': stamp,
                          'market_data_mode': 'REALTIME', 'ask': 100, 'bid': bid},
                'target_kind': 'FIRST_MEANINGFUL_RESISTANCE', 'inputs': values, 'attestations': attestations,
                'planned_holding_trading_days': 10,
                'portfolio': {'source': 'DEGIRO', 'currency': 'EUR', 'observed_utc': stamp,
                              'holdings_sha256': holdings_digest(positions), 'open_exposure_eur': 1000 if positions else 0,
                              'available_cash_eur': 50_000, 'pending_buy_eur': 0, 'pending_new_positions': 0,
                              **(capacity or {})}}

    def evaluate(self, payload, *, now=NOW, currency='EUR'):
        return evaluate_entry('TEST.PA', currency, self.sign(payload), now=now, reviewer_pin=self.pin)

    def test_exact_profit_boundary_and_whole_shares(self):
        result = self.evaluate(self.inputs())
        self.assertEqual((result['shares'], result['net_profit_eur']), (34, 150))
        self.assertEqual(result['status'], 'HUMAN_REVIEW_REQUIRED')
        self.assertFalse(result['trade_ready'])
        self.assertFalse(result['order_placement_enabled'])

    def test_net_profit_rejected_and_retained_in_report(self):
        evidence = {'TEST.PA': self.sign(self.inputs(target=104.5, buy=4, sell=4))}
        _, rows = assess_report(report(), evidence, now=NOW, reviewer_pin=self.pin)
        self.assertEqual(rows[0]['financial_entry']['net_profit_eur'], 145)
        self.assertEqual(rows[0]['recovery_phase'], DEGIRO_VERIFICATION)

    def test_first_resistance_already_passed_at_verified_ask_blocks_financial_promotion(self):
        payload = self.inputs(target=104.5)
        payload['quote']['ask'] = 105
        payload['attestations']['broker_quote']['fields']['broker_ask'] = 105
        _, rows = assess_report(report(), {'TEST.PA': self.sign(payload)}, now=NOW, reviewer_pin=self.pin)
        self.assertEqual(rows[0]['financial_entry']['resistance_room'],
                         {'status': 'PASSED', 'level': 104.5, 'price_basis': 'DEGIRO_ASK', 'remaining_pct': None})
        self.assertEqual(rows[0]['recovery_phase'], DEGIRO_VERIFICATION)

    def test_rounded_profit_and_rr_do_not_pass(self):
        result = self.evaluate(self.inputs(target=104.49999, buy=2, sell=1))
        self.assertEqual(result['net_profit_eur'], 150)
        self.assertFalse(result['checks']['net_profit_at_least_150_eur'])
        weak_rr = self.evaluate(self.inputs(target=106, invalidation=96.5))
        self.assertTrue(weak_rr['checks']['net_profit_at_least_150_eur'])
        self.assertFalse(weak_rr['checks']['net_rr_at_least_2'])

    def test_slippage_costs_and_no_new_broker_spread_cutoff(self):
        result = self.evaluate(self.inputs(bid=99.8, target=106.5, buy=4, sell=5, slip_buy=.1, slip_sell=.2))
        self.assertEqual((result['shares'], result['notional_with_buy_fee_eur'], result['net_profit_eur'],
                          result['net_risk_eur'], result['net_rr']), (34, 3407.4, 201.8, 70.2, 2.8746))
        wide = self.evaluate(self.inputs(bid=99, target=106.5, buy=4, sell=5))
        self.assertEqual(wide['status'], 'HUMAN_REVIEW_REQUIRED')
        self.assertEqual(self.evaluate(self.inputs(bid=101))['status'], 'STRUCTURE_BLOCKED')

    def test_isla_identity_missing_or_mismatched_is_blocked(self):
        for field, value in (('symbol', 'ISLA'), ('isin', None), ('operating_mic', None), ('identity_verified', False)):
            with self.subTest(field=field):
                payload = self.inputs()
                payload['instrument'][field] = value
                self.assertEqual(self.evaluate(payload)['reason'], 'INSTRUMENT_IDENTITY_UNVERIFIED_OR_MISMATCHED')
        self.assertEqual(self.evaluate(self.inputs(), currency='GBP')['reason'], 'EUR_LISTING_REQUIRED')

    def test_evidence_expiry_future_and_tampering(self):
        self.assertEqual(self.evaluate(self.inputs(), now=NOW + timedelta(seconds=120))['status'], 'HUMAN_REVIEW_REQUIRED')
        for seconds in (-1, 121):
            self.assertEqual(self.evaluate(self.inputs(), now=NOW + timedelta(seconds=seconds))['reason'],
                             'BROKER_QUOTE_STALE_OR_FUTURE')
        signed = self.sign(self.inputs())
        signed['payload']['quote']['bid'] = 99.7
        self.assertEqual(evaluate_entry('TEST.PA', 'EUR', signed, now=NOW, reviewer_pin=self.pin)['reason'],
                         'BROKER_REVIEW_SIGNATURE_UNVERIFIED')

    def test_forged_financial_report_claim_degrades_and_valid_evidence_promotes(self):
        data, state = report(), {'signals': {}}
        data['candidates'][0].update(recovery_phase=FINANCIAL_ENTRY_CONFIRMED,
                                     financial_entry={'status': 'HUMAN_REVIEW_REQUIRED'})
        self.assertIn(DEGIRO_VERIFICATION, self.send(data, state=state)[0][1])
        evidence = {'TEST.PA': self.sign(self.inputs())}
        outcome = self.send(data, state=state, evidence=evidence, pin=self.pin)
        self.assertIn(FINANCIAL_ENTRY_CONFIRMED, outcome[0][1])
        self.assertIn('150.00', outcome[0][1])

    def test_unreviewed_target_kind_and_missing_slippage_block_confirmation(self):
        payload = self.inputs()
        payload['target_kind'] = 'FURTHER_RESISTANCE'
        self.assertEqual(self.evaluate(payload)['reason'], 'BROKER_SOURCE_OR_FIRST_RESISTANCE_UNVERIFIED')
        payload = self.inputs()
        del payload['inputs']['buy_slippage_per_share']
        self.assertEqual(self.evaluate(payload)['reason'], 'VALUE_MISMATCH')

    def test_seventh_position_does_not_get_financial_promotion(self):
        holdings = {f'HELD{i}.PA': {'shares': 5} for i in range(6)}
        evidence = {'TEST.PA': self.sign(self.inputs(positions=holdings))}
        sent = self.send(report(), holdings=holdings, positions=holdings, evidence=evidence, pin=self.pin)
        self.assertIn(DEGIRO_VERIFICATION, sent[0][1])
        self.assertNotIn(FINANCIAL_ENTRY_CONFIRMED, sent[0][1])

    def test_quote_observed_now_with_delayed_market_timestamp_is_blocked(self):
        payload = self.inputs()
        payload['quote']['market_utc'] = (NOW - timedelta(minutes=15)).isoformat()
        self.assertEqual(self.evaluate(payload)['reason'], 'BROKER_MARKET_TIMESTAMP_UNVERIFIED_OR_DELAYED')
        payload = self.inputs()
        payload['quote']['market_data_mode'] = 'DELAYED'
        self.assertEqual(self.evaluate(payload)['reason'], 'BROKER_MARKET_TIMESTAMP_UNVERIFIED_OR_DELAYED')

    def test_capacity_binds_holdings_and_blocks_total_exposure_pending_cash_and_horizon(self):
        positions = {'US': {'shares': 9, 'provider_symbol': 'AAA'}}
        for changes, expected in (
                ({'open_exposure_eur': 47_000}, 'CAPITAL_LIMIT_EXCEEDED'),
                ({'open_exposure_eur': 45_000, 'pending_buy_eur': 2_000}, 'CAPITAL_LIMIT_EXCEEDED'),
                ({'available_cash_eur': 3_000}, 'AVAILABLE_CASH_INSUFFICIENT'),
                ({'observed_utc': (NOW - timedelta(seconds=121)).isoformat()}, 'REVIEWED_CAPACITY_STALE_OR_FUTURE'),
                ({'holdings_sha256': '0' * 64}, 'CAPACITY_HOLDINGS_MISMATCH')):
            with self.subTest(reason=expected):
                proof = self.sign(self.inputs(positions=positions, capacity=changes))
                result = evaluate_entry('TEST.PA', 'EUR', proof, now=NOW, reviewer_pin=self.pin, positions=positions)
                self.assertEqual(result['portfolio_capacity']['status'], expected)
                self.assertEqual(result['net_profit_eur'], 150)
        payload = self.inputs(positions=positions)
        payload['planned_holding_trading_days'] = 16
        result = evaluate_entry('TEST.PA', 'EUR', self.sign(payload), now=NOW, reviewer_pin=self.pin, positions=positions)
        self.assertEqual(result['portfolio_capacity']['status'], 'HOLDING_HORIZON_UNVERIFIED')

    def test_strong_signal_precedes_priority_watch_and_second_advisory_respects_six_slots(self):
        holdings = {f'HELD{i}.PA': {'shares': 5} for i in range(5)}
        symbols = ('KER.PA', 'SU.PA', 'TEST.PA', 'ZZ.PA')
        data = report(symbols=symbols)
        data['candidates'][2]['early_recovery_score'] = 5
        data['candidates'][0]['broker_verify_now'] = False
        data['candidates'][1]['broker_verify_now'] = False
        evidence = {name: self.sign(self.inputs(symbol=name, positions=holdings)) for name in symbols[2:]}
        sent = self.send(data, holdings=holdings, positions=holdings, evidence=evidence, pin=self.pin)
        self.assertEqual(sent[0][0], 'TEST.PA')
        self.assertIn(FINANCIAL_ENTRY_CONFIRMED, sent[0][1])
        self.assertIn(DEGIRO_VERIFICATION, sent[1][1])
        self.assertEqual(sum(FINANCIAL_ENTRY_CONFIRMED in body for _, body in sent), 1)

    def test_historical_gross_and_missing_resistance_do_not_block_broker_check(self):
        from europe_combined_recovery_report import combine
        data = combine({'candidates': [{'symbol': 'TEST.PA', 'currency': 'EUR',
                                        'research_flags': ['MEANINGFUL-RESISTANCE-UNRESOLVED'],
                                        'historical_3500_eur_scenarios': {'rr_to_meaningful': 1, 'meaningful_resistance_gross_eur': 30}}]},
                       {'candidates': [{'symbol': 'TEST.PA', 'early_recovery_score': 4, 'higher_last_low': True,
                                        'data_status': 'INTRADAY-RESEARCH-ONLY',
                                        'latest_bar': {'time': (NOW - timedelta(minutes=15)).isoformat()}}]},
                       {'candidates': [{'symbol': 'TEST.PA', 'provider_delayed_but_usable_for_attention': True,
                                        'quote_utc': (NOW - timedelta(minutes=10)).isoformat()}]}, now=NOW)
        self.assertIn(DEGIRO_VERIFICATION, self.send(data)[0][1])
        evidence = {'TEST.PA': self.sign(self.inputs())}
        self.assertIn(FINANCIAL_ENTRY_CONFIRMED, self.send(data, evidence=evidence, pin=self.pin)[0][1])

    def test_R08_decline_releases_exact_reservation_once_and_preserves_limits(self):
        positions = {f'HELD{i}.PA': {'shares': 5} for i in range(5)}
        data = report(symbols=('TEST.PA', 'ZZ.PA', 'OTHER.PA'))
        data['candidates'][0]['early_recovery_score'] = 5
        state, store, sent = {'signals': {}}, Store(), []
        proofs = {row['symbol']: self.sign(self.inputs(symbol=row['symbol'], positions=positions,
                                                         capacity={'open_exposure_eur': 46_000, 'available_cash_eur': 4_000}))
                  for row in data['candidates']}

        def run(payload, releases=()):
            options = {'evidence': proofs, 'reviewer_pin': self.pin, 'clock': lambda: NOW, 'positions': positions}
            if releases:
                options['capacity_declines'] = releases
            notify_eu_research(store, state, payload, set(positions),
                               sender=lambda symbol, body: sent.append((symbol, body)), **options)

        run({'generated_utc': data['generated_utc'], 'candidates': data['candidates'][:1]})
        key = f'EU-RESEARCH|TEST.PA|FINANCIAL_ENTRY_CONFIRMED|{NOW.date().isoformat()}'
        record = state['signals'][key]
        decline = {'reservation_key': key, 'notified_utc': record['notified_utc'], 'decided_utc': NOW.isoformat()}
        run(data)
        results = {row['symbol']: row for row in state['latest_eu_entry_evaluation']['financial_results']}
        self.assertEqual(results['ZZ.PA']['portfolio_capacity']['status'], 'POSITION_LIMIT_EXCEEDED')
        self.assertEqual([symbol for symbol, body in sent if FINANCIAL_ENTRY_CONFIRMED in body], ['TEST.PA'])
        run(data, [{**decline, 'notified_utc': (NOW - timedelta(seconds=1)).isoformat()},
                   {**decline, 'decided_utc': (NOW + timedelta(seconds=1)).isoformat()}])
        self.assertNotIn('capacity_released_utc', record)
        run(data, [decline, decline])
        run(data, [decline])
        financial = [symbol for symbol, body in sent if FINANCIAL_ENTRY_CONFIRMED in body]
        self.assertEqual(len(financial), 2)
        self.assertEqual(financial[0], 'TEST.PA')
        self.assertEqual(state['signals'][key]['delivery'], 'sent')
        self.assertEqual(state['signals'][key]['capacity_released_utc'], NOW.isoformat())

    def test_broker_evidence_that_expires_while_reserving_cannot_send(self):
        evidence = {'TEST.PA': self.sign(self.inputs())}
        state, times = {'signals': {}}, [NOW + timedelta(seconds=119)]
        store = Store(after_save=lambda: times.append(NOW + timedelta(seconds=121)))
        self.assertEqual(self.send(report(), state=state, store=store, evidence=evidence, pin=self.pin,
                                   clock=lambda: times[-1]), [])
        self.assertEqual(next(iter(state['signals'].values()))['delivery'], 'expired_before_send')
        self.assertIn(DEGIRO_VERIFICATION, self.send(report(), state=state, now=times[-1],
                                                    evidence=evidence, pin=self.pin)[0][1])

    def test_actual_report_subprocess_to_private_store_to_mock_sender(self):
        now = datetime.now(timezone.utc)
        private = Store({'signals': {}, EVIDENCE_STATE_KEY: {'TEST.PA': self.sign(self.inputs(now=now))}})
        prealert, us = Store(), Store()
        sent = []
        baseline = Path.cwd()
        with tempfile.TemporaryDirectory() as folder:
            try:
                os.chdir(folder)
                Path('reports').mkdir()
                Path('config').mkdir()
                inputs = {
                    'europe_swing_research.json': {'candidates': [{'symbol': 'TEST.PA', 'currency': 'EUR',
                        'historical_3500_eur_scenarios': {'rr_to_meaningful': 2.5, 'meaningful_resistance_gross_eur': 180}}]},
                    'europe_intraday_confirmation.json': {'candidates': [{'symbol': 'TEST.PA',
                        'higher_last_low': True, 'data_status': 'INTRADAY-RESEARCH-ONLY', 'early_recovery_score': 4,
                        'latest_bar': {'time': (now - timedelta(minutes=15)).isoformat()}}]},
                    'europe_quote_execution_audit.json': {'candidates': [{'symbol': 'TEST.PA',
                        'provider_delayed_but_usable_for_attention': True,
                        'quote_utc': (now - timedelta(minutes=12)).isoformat()}]},
                    'manual_recovery_trigger_report.json': {'rows': []}, 'profit_exit_watch_report.json': {'rows': []},
                }
                for name, raw in inputs.items():
                    (Path('reports') / name).write_text(json.dumps(raw))
                Path('config/profit_exit_watch.json').write_text('{"positions": {}}')

                def scanner(script, **kwargs):
                    if script == 'europe_combined_recovery_report.py':
                        subprocess.run([sys.executable, ROOT / script], capture_output=True, check=True)

                def deliver(*args, **kwargs):
                    return notify_eu_research(*args, **kwargs, sender=lambda *item: sent.append(item))

                with patch.object(safe_runner, 'PrivateStore', side_effect={'eu': private, 'prealert': prealert, 'us': us}.get), \
                        patch.object(safe_runner, 'hydrate'), patch.object(safe_runner, 'sync_canonical_positions'), \
                        patch.object(safe_runner, 'run', side_effect=scanner), patch.object(safe_runner, 'notify'), \
                        patch.object(safe_runner, 'notify_eu_research', side_effect=deliver), \
                        patch('company_event_watch.notify_events'), patch('silent_macro_context.update_silent_context'), \
                        patch('dipsaus_fx_source.fetch_fx', return_value={'status': 'FX_UNAVAILABLE'}), \
                        patch.dict(os.environ, {REVIEWER_PIN_ENV: self.pin, 'SCANNER_NOTIFICATIONS_ENABLED': 'true'}):
                    with patch('sys.argv', ['safe_runner.py', 'eu']):
                        safe_runner.main()
                    self.assertEqual(private.load()['latest_eu_report']['candidates'][0]['recovery_phase'], FINANCIAL_ENTRY_CONFIRMED)
                    with patch('sys.argv', ['safe_runner.py', 'prealert', '--live']):
                        safe_runner.main()
                    key, prior = next((key, item) for key, item in prealert.load()['signals'].items()
                                      if key.startswith('EU-RESEARCH|'))
                    decision = {'reservation_key': key, 'notified_utc': prior['notified_utc'],
                                'decided_utc': datetime.now(timezone.utc).isoformat()}
                    Path('config/notification_quality_gate.json').write_text(json.dumps({'eu_capacity_declines': [decision]}))
                    with patch('sys.argv', ['safe_runner.py', 'prealert', '--live']):
                        safe_runner.main()
                    self.assertEqual(prealert.load()['signals'][key]['capacity_released_utc'], decision['decided_utc'])
                    self.assertEqual(len(sent), 1)
                self.assertIn(FINANCIAL_ENTRY_CONFIRMED, sent[0][1])
                self.assertEqual(prealert.load()['latest_notification_diagnostics']['eu_recovery_phase_counts'][FINANCIAL_ENTRY_CONFIRMED], 1)
            finally:
                os.chdir(baseline)


if __name__ == '__main__':
    unittest.main()
