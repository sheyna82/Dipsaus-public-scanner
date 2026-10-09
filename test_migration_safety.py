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
        return {'symbol': 'TEST', 'market': 'US', 'watch_type': 'AUTO-US-DISCOVERY',
                'prealert_trigger_observed': True, 'breakout_observed': True, 'provider_quote': 42}

    def test_shadow_private_owner_blocks_notifications(self):
        with self.assertRaises(RuntimeError):
            notify(Store(False), {'signals': {}}, [self.entry()], [], lambda *a: self.fail('sent'))

    def test_duplicate_phase_silent(self):
        store = Store(); state = {'signals': {}}; sent = []
        notify(store, state, [self.entry(), self.entry()], [], lambda *a: sent.append(a))
        self.assertEqual(len(sent), 1)
        self.assertEqual(store.saved[0]['signals']['ENTRY|US|TEST|PHASE']['delivery'], 'reserved')

    def test_seeded_phase_silent(self):
        state = {'signals': {'ENTRY|US|TEST|PHASE': {'phase': 'BREAKOUT-SEEN'}}}
        notify(Store(), state, [self.entry()], [], lambda *a: self.fail('duplicate'))

    def test_uncertain_delivery_not_retried(self):
        state = {'signals': {}}; store = Store()
        def fail(*args): raise TimeoutError()
        with self.assertRaises(TimeoutError): notify(store, state, [self.entry()], [], fail)
        notify(store, state, [self.entry()], [], lambda *a: self.fail('duplicate'))

    def test_profit_rearms_only_when_condition_clears(self):
        state = {'signals': {}}; store = Store(); sent = []
        row = {'symbol': 'TEST', 'profit_alert': True, 'alert_reason': 'RESISTANCE', 'decision': 'CHECK'}
        send = lambda *a: sent.append(a)
        notify(store, state, [], [row, row], send)
        notify(store, state, [], [{'symbol': 'TEST', 'profit_alert': False}, row], send)
        self.assertEqual(len(sent), 2)

    def test_unconfirmed_bottom_silent(self):
        row = self.entry(); row['breakout_observed'] = False
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
            'TEST': {'currency': 'USD', 'route_2_breakout': {'break_above_usd': 40}}}},
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

    def test_eu_no_old_artifact_restore(self):
        import europe_swing_research as eu
        with patch.object(eu, 'SOURCE', Path('/nonexistent/dipsaus-fresh-data')):
            with self.assertRaises(RuntimeError): eu.restore()


if __name__ == '__main__': unittest.main()
