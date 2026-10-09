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
from private_notifications import notify


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
    args = parser.parse_args()
    hydrate()
    store = PrivateStore(args.mode); state = store.load()
    if args.live:
        if args.mode != 'prealert' or os.environ.get('SCANNER_NOTIFICATIONS_ENABLED') != 'true':
            raise RuntimeError('LIVE_NOTIFICATIONS_NOT_ENABLED')
        store.require_exclusive_sender()
    routes = PrivateStore('us').load().get('us_routes') if args.mode == 'prealert' else state.get('us_routes')
    if routes is not None:
        Path('config/us_live_trigger_routes.json').write_text(json.dumps(routes))
    if args.mode == 'prealert':
        run('manual_recovery_trigger_watch.py'); run('profit_exit_watch.py')
        # Retain the existing recheck while avoiding a public summary or artifacts.
        run('manual_recovery_trigger_watch.py')
        entries = json.loads(Path('reports/manual_recovery_trigger_report.json').read_text())
        exits = json.loads(Path('reports/profit_exit_watch_report.json').read_text())
        state['latest_watch_reports'] = {'entries': entries, 'exits': exits}
        store.save(state)
        if args.live: notify(store, state, entries['rows'], exits['rows'])
    elif args.mode == 'eu':
        # Original EU refresh can fail its quality gate while still saving an audited database.
        try: run('europe_ohlcv_pilot.py')
        except RuntimeError:
            if not Path('reports/europe_ohlcv.jsonl.gz').exists(): raise
        for script in ('europe_raw_source_comparison.py', 'europe_independent_supplement.py',
                       'europe_swing_research.py', 'europe_intraday_confirmation.py',
                       'europe_quote_execution_audit.py', 'europe_combined_recovery_report.py'):
            run(script)
        state['latest_eu_report'] = json.loads(Path('reports/europe_combined_recovery_report.json').read_text())
        store.save(state)
    else:
        run('us_momentum_recovery_discovery.py')
        now = datetime.now(timezone.utc)
        slots = {13: 0, 14: 1, 15: 2, 16: 3, 18: 4, 20: 5}
        start = (int(now.timestamp()) // 86400 + slots.get(now.hour, 0) * 7) % 21
        Path('reports/us_batch_runs').mkdir(parents=True, exist_ok=True)
        for i in range(7):
            batch = (start + i) % 21
            run('us_recovery_pilot.py', US_BATCH=batch)
            Path(f'reports/us_batch_runs/batch_{batch}.json').write_bytes(Path('reports/us_recovery_pilot.json').read_bytes())
        run('us_auto_prealert_handoff.py'); run('us_live_trigger_routes.py')
        state['us_routes'] = json.loads(Path('reports/us_live_trigger_routes.json').read_text())
        state['latest_us_reports'] = {p.name: json.loads(p.read_text()) for p in Path('reports/us_batch_runs').glob('*.json')}
        store.save(state)
    print('Scanner completed. Runtime details saved privately; notifications ' + ('enabled.' if args.live else 'disabled (shadow mode).'))


if __name__ == '__main__':
    try: main()
    except Exception as exc:
        # Only exception class is public. Neither payloads nor authenticated URLs escape.
        reason = str(exc) if isinstance(exc, RuntimeError) else ''
        if not re.fullmatch(r'(?:PRIVATE_(?:CONFIG|STATE)_[A-Z_0-9]+|STATE_[A-Z_]+|LIVE_NOTIFICATIONS_NOT_ENABLED|SCANNER_STEP_FAILED: [a-z_]+\.py)', reason):
            reason = type(exc).__name__
        print('SCANNER_BLOCKED: ' + reason, file=sys.stderr)
        sys.exit(1)
