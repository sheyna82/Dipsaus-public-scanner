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


def notification_diagnostics(entries, exits, eu_report, state, active_symbols):
    """Private aggregate-only diagnostics; no symbols, quotes, or personal data."""
    from collections import Counter
    from datetime import timedelta
    now = datetime.now(timezone.utc)
    reasons = Counter()
    entry_rows = entries.get('rows', [])
    exit_rows = exits.get('rows', [])
    eu_rows = eu_report.get('candidates', [])
    for row in entry_rows:
        if not row.get('prealert_trigger_observed'):
            reasons['entry_no_trigger'] += 1
        elif row.get('watch_type') == 'PORTFOLIO-REENTRY':
            reasons['entry_portfolio_reentry_gate'] += 1
        else:
            reasons['entry_triggered_for_notification_evaluation'] += 1
    for row in exit_rows:
        if row.get('symbol') not in active_symbols:
            reasons['exit_not_active_holding'] += 1
        elif not row.get('profit_alert'):
            reasons['exit_no_profit_alert'] += 1
        else:
            reasons['exit_alert_for_notification_evaluation'] += 1
    try:
        generated = datetime.fromisoformat(eu_report['generated_utc'].replace('Z', '+00:00'))
        fresh = generated.tzinfo is not None and timedelta(0) <= now - generated <= timedelta(minutes=25)
    except (KeyError, ValueError, TypeError):
        fresh = False
    if not fresh:
        reasons['eu_report_missing_or_stale'] = len(eu_rows) or 1
    else:
        for row in eu_rows:
            if not row.get('broker_verify_now') or not row.get('broker_check_candidate') or row.get('trade_ready'):
                reasons['eu_broker_gate'] += 1
            elif not (row.get('provider_freshness_pass') or row.get('provider_delayed_but_usable_for_attention')):
                reasons['eu_quote_freshness_gate'] += 1
            elif (row.get('early_recovery_score') or 0) < 3:
                reasons['eu_low_score_or_holding_exception'] += 1
            elif (row.get('historical_3500_eur_scenarios') or {}).get('rr_to_meaningful', 0) < 2:
                reasons['eu_risk_reward_gate'] += 1
            elif (row.get('historical_3500_eur_scenarios') or {}).get('meaningful_resistance_gross_eur', 0) < 150:
                reasons['eu_money_gate'] += 1
            else:
                reasons['eu_candidate_for_dedupe_and_cap'] += 1
    # Aggregate-only US/EU funnel: no ticker, position, quote, or private identifiers.
    market_counts = Counter()
    for row in entry_rows:
        market = 'US' if row.get('market') == 'US' else 'EU' if row.get('market') == 'EU' else 'OTHER'
        market_counts[market + '_examined'] += 1
        if row.get('watch_type') == 'AUTO-US-DISCOVERY':
            market_counts['us_auto_discovery_examined'] += 1
            if not row.get('phone_notification_eligible'):
                market_counts['us_auto_not_phone_eligible'] += 1
            elif not row.get('provider_freshness_pass'):
                market_counts['us_auto_stale_provider'] += 1
            elif not row.get('structure_available'):
                market_counts['us_auto_missing_structure'] += 1
            elif not row.get('early_turn_observed'):
                market_counts['us_auto_no_early_turn'] += 1
            elif row.get('status') == 'EARLY-RECOVERY-WATCH':
                market_counts['us_auto_early_notification_candidate'] += 1
            elif not row.get('prealert_trigger_observed'):
                market_counts['us_auto_no_prealert_trigger'] += 1
            else:
                market_counts['us_auto_prealert_triggered'] += 1
        elif row.get('prealert_trigger_observed'):
            market_counts[market.lower() + '_other_triggered'] += 1
    return {
        'market_funnel_counts': dict(sorted(market_counts.items())),
        'generated_utc': now.isoformat(),
        'entry_rows_examined': len(entry_rows),
        'exit_rows_examined': len(exit_rows),
        'eu_rows_examined': len(eu_rows),
        'eu_report_fresh': fresh,
        'reason_counts': dict(sorted(reasons.items())),
        'note': 'Aggregate diagnostic categories are nonexclusive of later dedupe and send gates; no trading filters changed.'
    }



def sync_private_notification_gate(store):
    """Load the canonical private notification gate without exposing it publicly.

    The GitHub Secret remains available for initial hydration, but the private
    repository file is authoritative for subsequent reviewed watchlist updates.
    Fail closed if it cannot be read or validated: never silently use a stale gate.
    """
    import base64
    import binascii
    record = store.request('/contents/config/notification_quality_gate.json')
    if not isinstance(record, dict) or record.get('encoding') != 'base64':
        raise RuntimeError('PRIVATE_CONFIG_GATE_INVALID_ENCODING')
    try:
        gate = json.loads(base64.b64decode(''.join(record['content'].split()), validate=True))
    except (KeyError, TypeError, ValueError, UnicodeError, binascii.Error):
        raise RuntimeError('PRIVATE_CONFIG_GATE_INVALID_SOURCE') from None
    if not isinstance(gate, dict) or not isinstance(gate.get('auto_us_notify_watchlist'), list) or not isinstance(gate.get('auto_us_silent_follow'), list):
        raise RuntimeError('PRIVATE_CONFIG_GATE_INVALID_SCHEMA')
    for key in ('auto_us_notify_watchlist', 'auto_us_silent_follow'):
        if any(not isinstance(symbol, str) or not symbol or len(symbol) > 24 for symbol in gate[key]):
            raise RuntimeError('PRIVATE_CONFIG_GATE_INVALID_SYMBOLS')
    Path('config/notification_quality_gate.json').write_text(json.dumps(gate))


def sync_canonical_positions(store, target):
    """Sync private canonical holdings, with safe stage-only error diagnostics."""
    import base64
    import binascii
    record = store.request('/contents/config/profit_exit_watch.json')
    if not isinstance(record, dict) or record.get('encoding') != 'base64':
        raise RuntimeError('PRIVATE_CONFIG_SYNC_INVALID_ENCODING')
    try:
        source = json.loads(base64.b64decode(''.join(record['content'].split()), validate=True))
    except (KeyError, TypeError, ValueError, UnicodeError, binascii.Error):
        raise RuntimeError('PRIVATE_CONFIG_SYNC_INVALID_SOURCE') from None
    if not isinstance(source, dict) or not isinstance(source.get('positions'), dict):
        raise RuntimeError('PRIVATE_CONFIG_SYNC_INVALID_POSITIONS') 
    positions = source['positions']
    if not positions or any(not isinstance(symbol, str) or not symbol or
           not isinstance(item, dict) or
           not isinstance(item.get('shares'), (int, float)) or
           isinstance(item.get('shares'), bool) or
           not (0 < item['shares'] < float('inf'))
           for symbol, item in positions.items()):
        raise RuntimeError('PRIVATE_CONFIG_SYNC_INVALID_HOLDINGS')
    try:
        current = json.loads(target.read_text())
    except (OSError, ValueError, UnicodeError):
        raise RuntimeError('PRIVATE_CONFIG_SYNC_INVALID_LOCAL_FILE') from None
    if not isinstance(current, dict) or not isinstance(current.get('positions'), dict):
        raise RuntimeError('PRIVATE_CONFIG_SYNC_INVALID_LOCAL_SCHEMA')
    current['positions'] = positions
    target.write_text(json.dumps(current))


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
    if args.mode in ('prealert', 'us') and type(store).__module__ == 'private_runtime':
        sync_private_notification_gate(store)
    if args.mode == 'prealert' and args.live:
        sync_canonical_positions(store, Path('config/profit_exit_watch.json'))

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
            holdings = {symbol for symbol, item in profit_cfg.get('positions', {}).items()
                        if isinstance(item, dict) and item.get('shares', 0) > 0}
            holdings.update(item.get('provider_symbol') for item in profit_cfg.get('positions', {}).values()
                            if isinstance(item, dict) and item.get('shares', 0) > 0 and item.get('provider_symbol'))
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
        # Shadow-only: connect only verified, time-stamped PRE-ALERT evidence.
        # Unconnected research gates remain UNKNOWN; never authorize notifications.
        from dipsaus_unified_research import evaluate as evaluate_unified_research
        from dipsaus_research_evidence import evidence_from_prealert
        research_now = datetime.now(timezone.utc)
        research_rows = [row for row in entries.get('rows', []) if isinstance(row, dict)][:200]
        state['latest_unified_research'] = {
            'generated_utc': research_now.isoformat(),
            'rows': [evaluate_unified_research(
                {'symbol': row.get('symbol')},
                evidence_from_prealert(row, entries.get('generated_utc'), research_now),
                now=research_now) for row in research_rows],
            'mode': 'SHADOW_RESEARCH_ONLY',
        }
        # Independently fetch fresh EUR/USD for private research only.
        # Never convert route breakout levels into verified resistance.
        from dipsaus_fx_source import fetch_fx
        try:
            import yfinance as yf
            fx_evidence = fetch_fx(yf, now=research_now)
        except ImportError:
            fx_evidence = {'status': 'FX_UNAVAILABLE'}
        state['latest_fx_research'] = {
            'generated_utc': research_now.isoformat(),
            'status': fx_evidence['status'],
            'mode': 'PRIVATE_RESEARCH_ONLY',
        }
        if fx_evidence['status'] == 'FX_FRESH':
            research_rows = [
                {**row, 'eur_per_usd': fx_evidence['eur_per_usd'],
                 'fx_checked_utc': fx_evidence['fx_checked_utc']}
                if row.get('market') == 'US' else row
                for row in research_rows
            ]
        # Keep gross-EUR potential private and research-only. No verified
        # resistance/invalidation/FX in the public PRE-ALERT feed => UNKNOWN.
        from dipsaus_eur_upside import estimate_gross_eur
        state['latest_eur_upside_research'] = {
            'generated_utc': research_now.isoformat(),
            'mode': 'SHADOW_RESEARCH_ONLY',
            'rows': [{'symbol': row.get('symbol'),
                      **estimate_gross_eur(row, now=research_now)}
                     for row in research_rows],
        }
        from dipsaus_eur_upside_audit import audit_rows as audit_eur_upside_rows
        state['latest_eur_upside_evidence_audit'] = {
            'generated_utc': research_now.isoformat(),
            **audit_eur_upside_rows(research_rows, now=research_now),
        }
        if not args.read_only:
            store.save(state)
        if args.live:
            before_sent = sum(1 for value in state.get('signals', {}).values()
                              if isinstance(value, dict) and value.get('delivery') == 'sent')
            active_exit_symbols = set(json.loads(Path('config/profit_exit_watch.json').read_text()).get('positions', {}))
            active_exits = [row for row in exits['rows'] if row.get('symbol') in active_exit_symbols]
            # Silent, private macro headline context: no additional phone messages. 
            from silent_macro_context import update_silent_context 
            update_silent_context(state)
            notify(store, state, entries['rows'], active_exits)
            # Dated company event reminders are research-only and deduplicated privately.
            from company_event_watch import notify_events
            notify_events(store, state)
            # Private EU discovery feeds broker-verification alerts, never trade-ready claims.
            eu_report = PrivateStore('eu').load().get('latest_eu_report', {})
            # An old EU discovery report must never produce actionable alerts.
            # Surface the stale dependency privately, without relaxing freshness.
            from datetime import timedelta
            try:
                eu_generated = datetime.fromisoformat(eu_report['generated_utc'].replace('Z', '+00:00'))
                eu_age = datetime.now(timezone.utc) - eu_generated
                eu_fresh = eu_generated.tzinfo is not None and timedelta(0) <= eu_age <= timedelta(minutes=25)
            except (KeyError, ValueError, TypeError):
                eu_fresh = False
            if not eu_fresh:
                # Diagnose the upstream refresh without publishing portfolio or
                # candidate details. Do not treat old EU research as live.
                try:
                    if eu_generated.tzinfo is None:
                        eu_reason = 'INVALID_TIMESTAMP'
                    elif eu_age.total_seconds() < 0:
                        eu_reason = 'FUTURE_TIMESTAMP'
                    else:
                        eu_reason = 'EXPIRED_REPORT'
                        eu_age_minutes = max(0, int(eu_age.total_seconds() // 60))
                except (NameError, TypeError, ValueError, OverflowError):
                    eu_reason = 'MISSING_OR_INVALID_REPORT'
                print('EU_REPORT_STALE: notification research skipped; EU refresh required. reason=' + eu_reason, flush=True)
                if eu_reason == 'EXPIRED_REPORT':
                    print('EU_REFRESH_LAG: age_minutes=' + str(eu_age_minutes) + ' allowed_minutes=25', flush=True)
            profit_cfg = json.loads(Path('config/profit_exit_watch.json').read_text())
            holdings = set()
            for symbol, item in profit_cfg.get('positions', {}).items():
                if isinstance(item, dict) and item.get('shares', 0) > 0:
                    holdings.add(item.get('provider_symbol') or symbol)
            notify_eu_research(store, state, eu_report, holdings)
            diagnostics = notification_diagnostics(entries, exits, eu_report, state, active_exit_symbols)
            diagnostics['new_confirmed_sends'] = sum(1 for value in state.get('signals', {}).values() if isinstance(value, dict) and value.get('delivery') == 'sent') - before_sent
            state['latest_notification_diagnostics'] = diagnostics
            store.save(state)
            # Public logs expose only aggregate funnel counts, never symbols or holdings.
            print('NOTIFICATION_MARKET_FUNNEL: ' + json.dumps(diagnostics['market_funnel_counts'], sort_keys=True), flush=True)
            print('NOTIFICATION_DIAGNOSTICS: private_aggregate_saved=true entry_rows=' + str(diagnostics['entry_rows_examined']) + ' exit_rows=' + str(diagnostics['exit_rows_examined']) + ' eu_rows=' + str(diagnostics['eu_rows_examined']), flush=True)
            after_sent = sum(1 for value in state.get('signals', {}).values()
                             if isinstance(value, dict) and value.get('delivery') == 'sent')
            print('NOTIFICATION_AUDIT: live=true new_confirmed_sends='
                  + str(max(0, after_sent - before_sent))
                  + ' (zero means no new qualifying alerts or deduplicated signals).', flush=True)
    elif args.mode == 'eu':
        # Original EU refresh can fail its quality gate while still saving an audited database.
        # Do not continue from an inherited OHLCV artifact when the current
        # provider refresh fails its coverage/freshness gate. A successful
        # downstream report must be based on a successful same-run refresh.
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

