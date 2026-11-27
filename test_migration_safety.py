import contextlib
import copy
import io
import json
import os
from pathlib import Path
import runpy
import tempfile
import unittest
from unittest.mock import patch
import pandas as pd
from datetime import datetime, timedelta, timezone
from private_runtime import hydrate, PrivateStore
from private_notifications import notify
from safe_runner import run


class Store:
    def __init__(self, exclusive=True):
        self.saved = []; self.exclusive = exclusive
    def save(self, state): self.saved.append(copy.deepcopy(state))
    def require_exclusive_sender(self):
        if not self.exclusive: raise RuntimeError('PRIVATE_SCANNER_STILL_ACTIVE')


class SafetyTests(unittest.TestCase):
    def entry(self):
        from test_us_notification_safety import us_row
        return us_row(hold_observed=False)


    def test_shadow_private_owner_blocks_notifications(self):
        with self.assertRaises(RuntimeError):
            notify(Store(False), {'signals': {}}, [self.entry()], [], lambda *a: self.fail('sent'))

    def test_duplicate_phase_silent(self):
        store = Store(); state = {'signals': {}}; sent = []
        notify(store, state, [self.entry(), self.entry()], [], lambda *a: sent.append(a))
        self.assertEqual(len(sent), 1)
        self.assertEqual(store.saved[0]['signals']['ENTRY|US|TEST|PHASE']['delivery'], 'reserved')

    def test_seeded_phase_silent(self):
        state = {'signals': {'ENTRY|US|TEST|PHASE': {'phase': 'BREAKOUT-HOLD-RETEST'}}}
        notify(Store(), state, [self.entry()], [], lambda *a: self.fail('duplicate'))

    def test_uncertain_delivery_not_retried(self):
        state = {'signals': {}}; store = Store()
        def fail(*args): raise TimeoutError()
        with self.assertRaises(TimeoutError):
            notify(store, state, [self.entry()], [], fail)
        self.assertEqual(state['signals']['ENTRY|US|TEST|PHASE']['delivery'], 'uncertain')
        self.assertEqual(store.saved[-1]['signals']['ENTRY|US|TEST|PHASE']['delivery'], 'uncertain')
        notify(store, state, [self.entry()], [], lambda *a: self.fail('duplicate'))

    def test_profit_deduplicates_same_day_after_brief_clear(self):
        state = {'signals': {}}; store = Store(); sent = []
        row = {'symbol': 'TEST', 'profit_alert': True, 'alert_reason': 'RESISTANCE', 'decision': 'CHECK'}
        send = lambda *a: sent.append(a)
        notify(store, state, [], [row, row], send)
        notify(store, state, [], [{'symbol': 'TEST', 'profit_alert': False}, row], send)
        self.assertEqual(len(sent), 1)

    def test_profit_new_material_reason_still_notifies(self):
        state = {'signals': {}}; store = Store(); sent = []
        row = {'symbol': 'TEST', 'profit_alert': True, 'alert_reason': 'RESISTANCE', 'decision': 'CHECK'}
        send = lambda *a: sent.append(a)
        notify(store, state, [], [row], send)
        changed = dict(row, alert_reason='STRUCTURE-DAMAGE')
        notify(store, state, [], [changed], send)
        self.assertEqual(len(sent), 2)

    def test_unconfirmed_bottom_silent(self):
        row = self.entry()
        row.update(breakout_observed=False, intraday_hold_confirmed=False, prealert_trigger_observed=False)
        notify(Store(), {'signals': {}}, [row], [], lambda *a: self.fail('bottom sent'))

    def test_split_secret_hydration_preserves_config(self):
        from private_runtime import SECRET_CONFIG
        bundle = {key: json.dumps({'test_marker': key}) for key in SECRET_CONFIG}
        previous = Path.cwd()
        with tempfile.TemporaryDirectory() as tmp:
            try:
                os.chdir(tmp)
                with patch.dict(os.environ, bundle, clear=True): hydrate()
                for key, filename in SECRET_CONFIG.items():
                    self.assertEqual(json.loads((Path('config')/filename).read_text())['test_marker'], key)
            finally: os.chdir(previous)

    def test_secret_path_traversal_rejected(self):
        with self.assertRaises(RuntimeError): hydrate('{"../exposed.json":{}}')

    def test_incomplete_secrets_fail_closed(self):
        with self.assertRaises(RuntimeError): hydrate('{}')

    def test_public_state_repository_rejected(self):
        with patch.dict(os.environ, {'SCANNER_STATE_REPOSITORY': 'owner/repo', 'SCANNER_STATE_TOKEN': 'synthetic'}):
            with patch.object(PrivateStore, 'request', return_value={'private': False}):
                with self.assertRaises(RuntimeError): PrivateStore()

    def test_subprocess_suppresses_private_output(self):
        with patch('safe_runner.subprocess.run') as mock:
            mock.return_value.returncode = 0
            run('test.py')
            self.assertEqual(mock.call_args.kwargs['stdout'], -3)
            self.assertEqual(mock.call_args.kwargs['stderr'], -3)

    def test_mocked_quote_watches_stale_and_fresh(self):
        root = Path(__file__).parent.resolve()
        now = datetime.now(timezone.utc)
        bundle = {'manual_recovery_triggers.json': {'candidates': {
            'TEST.PA': {'currency': 'EUR', 'route_2_breakout': {'break_above_eur': 40}}}},
            'profit_exit_watch.json': {'positions': {}},
            'portfolio_reentry_watch.json': {'candidates': {}},
            'notification_quality_gate.json': {}}
        previous = Path.cwd()
        with tempfile.TemporaryDirectory() as tmp:
            try:
                os.chdir(tmp); hydrate(json.dumps(bundle))
                for age, expected in ((30, True), (3600, False)):
                    frame = pd.DataFrame({'Close': [42.]}, index=pd.DatetimeIndex([now-timedelta(seconds=age)]))
                    with patch('yfinance.Ticker') as ticker, contextlib.redirect_stdout(io.StringIO()):
                        ticker.return_value.history.return_value = frame
                        runpy.run_path(str(root/'manual_recovery_trigger_watch.py'))
                    row = json.loads(Path('reports/manual_recovery_trigger_report.json').read_text())['rows'][0]
                    self.assertEqual(row['prealert_trigger_observed'], expected)
                    self.assertFalse(row['execution_ready'])
            finally: os.chdir(previous)

    def test_eu_runner_rejects_failed_refresh_even_with_old_artifact(self):
        import safe_runner
        from contextlib import chdir
        fake_store = Store()
        with tempfile.TemporaryDirectory() as folder, chdir(folder):
            Path('reports').mkdir()
            Path('reports/europe_combined_recovery_report.json').write_text('{"candidates": []}')
            with (patch('sys.argv', ['safe_runner.py', 'eu']), patch.object(safe_runner, 'hydrate'),
                  patch.object(safe_runner, 'PrivateStore', return_value=fake_store),
                  patch.object(fake_store, 'load', return_value={'signals': {}}, create=True),
                  patch.object(safe_runner, 'run', side_effect=RuntimeError('SCANNER_STEP_FAILED')) as scan):
                with self.assertRaisesRegex(RuntimeError, 'SCANNER_STEP_FAILED'):
                    safe_runner.main()
                scan.assert_called_once_with('europe_ohlcv_pilot.py')
            self.assertEqual(fake_store.saved, [])

    def test_eu_no_old_artifact_restore(self):
        import europe_swing_research as eu
        with patch.object(eu, 'SOURCE', Path('/nonexistent/dipsaus-fresh-data')):
            with self.assertRaises(RuntimeError): eu.restore()


class UsPhaseEvidenceTests(unittest.TestCase):
    def test_us_text_and_unbound_flags_cannot_claim_retest(self):
        from private_notifications import phase
        self.assertEqual(phase({'market': 'US', 'status': 'BREAKOUT RETEST TURN'}), 'BOTTOM-RECOVERY')
        self.assertEqual(phase({'market': 'US', 'breakout_observed': True, 'reclaim_observed': True,
                                'intraday_hold_confirmed': True}), 'CURRENT-RECOVERY-CONFIRMED')

if __name__ == '__main__': unittest.main()
