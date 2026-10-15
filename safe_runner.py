"""Run inherited scanner silently; keep personal configuration/reports off public surfaces."""
import argparse
import json
import os
import re
from pathlib import Path
import subprocess
import sys
from datetime import datetime, timezone
from private_runtime import hydrate, PrivateStore
from private_notifications import notify, notify_eu_research


def run(script, **extra):
    env = dict(os.environ, **{k: str(v) for k, v in extra.items()})
    # Suppress stdout, stderr and tracebacks containing holdings, API URLs or contact data.
    result = subprocess.run([sys.executable, script], env=env,
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=1500)
    if result.returncode:
        raise RuntimeError('SCANNER_STEP_FAILED: ' + script)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=['prealert', 'eu', 'us'])
    parser.add_argument('--live', action='store_true')
    parser.add_argument('--read-only', action='store_true')
    args = parser.parse_args()
    if args.read_only and (args.live or args.mode != 'prealert'):
        raise RuntimeError('READ_ONLY_MODE_INVALID')
    hydrate()
    store = PrivateStore(args.mode); state = store.load()
    if args.mode == 'prealert' and args.live:
        # The live secret can lag behind the private canonical profit-watch file.
        # Synchronize EXE only, in memory, without exposing holdings to public logs.
        import base64
        record = store.request('/contents/config/profit_exit_watch.json')
        if record.get('encoding') != 'base64':
            raise RuntimeError('PRIVATE_CONFIG_SYNC_INVALID')
        source = json.loads(base64.b64decode(record['content']))
        source_exe = (source.get('positions') or {}).get('EXE')
        target = Path('config/profit_exit_watch.json')
        current = json.loads(target.read_text())
        if not isinstance(source_exe, dict) or source_exe.get('shares') != 114 or source_exe.get('currency') != 'USD':
            raise RuntimeError('PRIVATE_CONFIG_SYNC_INVALID')
        if 'EXE' not in current.get('positions', {}):
            raise RuntimeError('PRIVATE_CONFIG_SYNC_INVALID')
        current['positions']['EXE'] = source_exe
        # Canonical private holdings are authoritative for exit alerts.
        # Never retain sold positions from a lagging runtime secret.
        for symbol in list(current['positions']):
            if symbol not in (source.get('positions') or {}):
                del current['positions'][symbol]
        target.write_text(json.dumps(current))

    if args.live:
        if args.mode != 'prealert' or os.environ.get('SCANNER_NOTIFICATIONS_ENABLED') != 'true':
            raise RuntimeError('LIVE_NOTIFICATIONS_NOT_ENABLED')
        store.require_exclusive_sender()
    routes = PrivateStore('us').load().get('us_routes') if args.mode == 'prealert' else state.get('us_routes')
    if routes is not None:
        Path('config/us_live_trigger_routes.json').write_text(json.dumps(routes))
    if args.mode == 'prealert':
        Path('config').mkdir(exist_ok=True)
        Path('config/profit_watch_state.json').write_text(json.dumps(state.get('profit_watch_state', {})))
        # Private configuration is present after hydrate in live runs, but not
        # in isolated regression tests. Reconcile only when both exist.
        profit_path = Path('config/profit_exit_watch.json')
        portfolio_path = Path('config/portfolio_reentry_watch.json')
        if profit_path.exists() and portfolio_path.exists():
            profit_cfg = json.loads(profit_path.read_text())
            holdings = {item.get('provider_symbol') or symbol
                        for symbol, item in profit_cfg.get('positions', {}).items()
                        if isinstance(item, dict) and item.get('shares', 0) > 0}
            portfolio_cfg = json.loads(portfolio_path.read_text())
            portfolio_cfg['candidates'] = {
                symbol: item for symbol, item in portfolio_cfg.get('candidates', {}).items()
                if symbol in holdings
            }
            portfolio_path.write_text(json.dumps(portfolio_cfg))
        run('manual_recovery_trigger_watch.py'); run('profit_exit_watch.py')
        # Retain the existing recheck while avoiding a public summary or artifacts.
        run('manual_recovery_trigger_watch.py')
        entries = json.loads(Path('reports/manual_recovery_trigger_report.json').read_text())
        exits = json.loads(Path('reports/profit_exit_watch_report.json').read_text())
        state['profit_watch_state'] = exits.pop('dynamic_state', state.get('profit_watch_state', {}))
        state['latest_watch_reports'] = {'entries': entries, 'exits': exits}
        if not args.read_only:
            store.save(state)
        if args.live:
            before_sent = sum(1 for value in state.get('signals', {}).values()
                              if isinstance(value, dict) and value.get('delivery') == 'sent')
            active_exit_symbols = set(json.loads(Path('config/profit_exit_watch.json').read_text()).get('positions', {}))
            notify(store, state, entries['rows'], [row for row in exits['rows'] if row.get('symbol') in active_exit_symbols])
            # Private EU discovery feeds broker-verification alerts, never trade-ready claims.
            eu_report = PrivateStore('eu').load().get('latest_eu_report', {})
            profit_cfg = json.loads(Path('config/profit_exit_watch.json').read_text())
            holdings = set()
            for symbol, item in profit_cfg.get('positions', {}).items():
                if isinstance(item, dict) and item.get('shares', 0) > 0:
                    holdings.add(item.get('provider_symbol') or symbol)
            notify_eu_research(store, state, eu_report, holdings)
            after_sent = sum(1 for value in state.get('signals', {}).values()
                             if isinstance(value, dict) and value.get('delivery') == 'sent')
            print('NOTIFICATION_AUDIT: live=true new_confirmed_sends='
                  + str(max(0, after_sent - before_sent))
                  + ' (zero means no new qualifying alerts or deduplicated signals).', flush=True)
    elif args.mode == 'eu':
        # Original EU refresh can fail its quality gate while still saving an audited database.
        # A failed EU refresh must never silently reuse old market data.
        run('europe_ohlcv_pilot.py')
        for script in ('europe_raw_source_comparison.py', 'europe_independent_supplement.py',
                       'europe_swing_research.py', 'europe_intraday_confirmation.py',
                       'europe_quote_execution_audit.py', 'europe_combined_recovery_report.py'):
            run(script)
        state['latest_eu_report'] = json.loads(Path('reports/europe_combined_recovery_report.json').read_text())
        store.save(state)
    else:
        run('us_momentum_recovery_discovery.py')
        # Advance by completed sweeps, not UTC day/hour. This guarantees that
        # three successful US sweeps cover all 21 batches, even if jobs run late.
        start = int(state.get('us_next_batch', 0)) % 21
        Path('reports/us_batch_runs').mkdir(parents=True, exist_ok=True)
        for i in range(7):
            batch = (start + i) % 21
            run('us_recovery_pilot.py', US_BATCH=batch)
            Path(f'reports/us_batch_runs/batch_{batch}.json').write_bytes(Path('reports/us_recovery_pilot.json').read_bytes())
        run('us_auto_prealert_handoff.py'); run('us_live_trigger_routes.py')
        state['us_routes'] = json.loads(Path('reports/us_live_trigger_routes.json').read_text())
        state['latest_us_reports'] = {p.name: json.loads(p.read_text()) for p in Path('reports/us_batch_runs').glob('*.json')}
        state['us_last_completed_batches'] = [(start + i) % 21 for i in range(7)]
        state['us_next_batch'] = (start + 7) % 21
        store.save(state)
    print('Scanner completed. ' + ('Read-only test; ' if args.read_only else 'Runtime details saved privately; ') + 'notifications ' + ('enabled.' if args.live else 'disabled (shadow mode).'))


if __name__ == '__main__':
    try: main()
    except Exception as exc:
        # Only exception class is public. Neither payloads nor authenticated URLs escape.
        reason = str(exc) if isinstance(exc, RuntimeError) else ''
        if not re.fullmatch(r'(?:PRIVATE_(?:CONFIG|STATE)_[A-Z_0-9]+|STATE_[A-Z_]+|LIVE_NOTIFICATIONS_NOT_ENABLED|SCANNER_STEP_FAILED: [a-z_]+\.py)', reason):
            reason = type(exc).__name__
        print('SCANNER_BLOCKED: ' + reason, file=sys.stderr)
        sys.exit(1)

