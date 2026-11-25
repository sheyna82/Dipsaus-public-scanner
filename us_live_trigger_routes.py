#!/usr/bin/env python3
"""Build and evaluate independent live recovery routes for US PRE-ALERT."""
import json
from datetime import datetime, timezone
from pathlib import Path

from eu_entry_net import age_seconds
from us_auto_prealert_handoff import DISABLED, read_report
from us_intraday_recovery import intraday_structure
from us_yahoo_bars import number

SRC = Path('reports/us_auto_prealert_candidates.json')
OUT = Path('reports/us_live_trigger_routes.json')
GATE = Path('config/notification_quality_gate.json')


def build_routes(handoff, gate, *, now):
    watchlist = set(gate.get('auto_us_notify_watchlist', [])) | {'GEHC'}
    silent_follow = set(gate.get('auto_us_silent_follow', []))
    rows = []
    for candidate in handoff.get('rows', []):
        if not candidate.get('auto_promoted'):
            continue
        symbol = candidate['symbol']
        evidence = candidate['routes']
        fast, deep = evidence.get('fast', {}), evidence.get('deep', {})
        fast_structure = fast.get('intraday_structure') or {}
        first_zone = (deep.get('historical_overhead_zones') or [{}])[0]
        deep_space = deep.get('space_to_first_overhead_pct')
        deep_quality = bool(deep.get('auto_promoted') and deep['bottom_signal_count'] >= 4
                            and deep['identity_status'] == 'NAME_CONSISTENT_UNVERIFIED'
                            and number(deep_space) and deep_space >= 3)
        fast_drawdown, change = fast.get('recent_drawdown_pct'), fast.get('day_change_pct')
        fast_quality = bool(fast_structure.get('early_recovery_observed') is True
                            and number(fast_drawdown) and fast_drawdown <= -8
                            and number(change) and change >= 1)
        disputed = deep.get('identity_status') == 'IDENTITY_MISMATCH'
        eligible = (symbol not in silent_follow and not disputed
                    and (symbol in watchlist or deep_quality or fast_quality))
        live_routes = {}
        if fast:
            live_routes['fast'] = {'level': fast_structure.get('first_rebound_high'),
                                   'floor': fast_structure.get('recovery_low'),
                                   'floor_ts': fast_structure.get('recovery_low_ts')}
        if deep.get('auto_promoted'):
            live_routes['deep'] = {'level': first_zone.get('low_usd'),
                                   'zone': [first_zone.get('low_usd'), first_zone.get('high_usd')],
                                   'floor': deep.get('historical_invalidation_reference_usd')}
        rows.append({'symbol': symbol, 'name': candidate.get('name'), 'observed_utc': now.isoformat(),
                     'status': 'PRE-ALERT' if eligible else 'SILENT-FOLLOW',
                     'phone_notification_eligible': eligible, 'silent_follow': not eligible,
                     'automatic_quality_promoted': deep_quality, 'fast_research_quality_promoted': fast_quality,
                     'identity_disputed': disputed, 'discovery_evidence': evidence, 'live_routes': live_routes,
                     'route_is_execution_signal': False, **DISABLED})
    return {'generated_utc': now.isoformat(), 'scope': 'US recovery research and live monitoring', 'rows': rows, **DISABLED}


def retain_recent_routes(report, previous, *, now):
    """Keep a bounded watchlist between rotating discovery sweeps."""
    symbols = {row['symbol'] for row in report['rows']}
    older = []
    for row in previous.get('rows', []):
        if not isinstance(row, dict) or not row.get('symbol') or row['symbol'] in symbols:
            continue
        age = age_seconds(row.get('observed_utc') or previous.get('generated_utc'), now)
        if age is not None and 0 <= age <= 7 * 86400:
            symbols.add(row['symbol'])
            older.append((age, row))
    older.sort(key=lambda item: (not item[1].get('phone_notification_eligible'), item[0], item[1]['symbol']))
    # Prior eligibility may have been explicitly revoked in current private config.
    # Retained names remain visible, with phone eligibility re-earned by a new sweep.
    retained = [{**row, 'phone_notification_eligible': False, 'silent_follow': True,
                 'status': 'SILENT-FOLLOW', 'retained_from_prior_sweep': True,
                 'observed_utc': row.get('observed_utc') or previous.get('generated_utc')}
                for _, row in older[:30]]
    return {**report, 'rows': report['rows'] + retained}


def floor_breach(bars, floor, *, floor_ts=None, known=None):
    if not number(floor) or floor <= 0:
        return known
    latest = known if type(known) is int else None
    after = max((stamp for stamp in (floor_ts, latest) if type(stamp) is int), default=0)
    was_below = latest is not None
    for bar in bars:
        if bar['ts'] <= after:
            continue
        below = bar['low'] < floor
        if below and not was_below:
            latest = bar['ts']
        was_below = below
    return latest


def monitor_recovery(item, snapshot, *, prior_alert=None):
    """Evaluate live evidence and discard old setups upon a breach or time gap."""
    if snapshot['symbol'] != item['symbol']:
        raise ValueError('WATCH_SNAPSHOT_SYMBOL_MISMATCH')
    bars = snapshot['bars']
    last = snapshot['latest_completed_bar']
    price = last['close']
    eligible = item.get('phone_notification_eligible') is True
    result = {'symbol': item['symbol'], 'market': 'US', 'watch_type': 'AUTO-US-DISCOVERY',
              'phone_notification_eligible': eligible, 'provider_quote': price,
              'provider_quote_utc': datetime.fromtimestamp(last['ts'], timezone.utc).isoformat(),
              'provider_quote_age_seconds': snapshot['bar_age_seconds'], 'provider_freshness_pass': snapshot['fresh'],
              'provider_reference': snapshot['reference'], 'completed_minute_bar': last,
              'provider_source': snapshot['source'], 'source_verified': False,
              'contiguous_completed_bars': len(bars), **DISABLED}
    configured_routes = item.get('live_routes')
    if not isinstance(configured_routes, dict):
        # An old report can supply a research floor, but old quote-based
        # thresholds cannot confirm a current recovery.
        configured_routes = {'legacy': {'floor': item.get('historical_invalidation_reference_usd')}}
    prior_alert = prior_alert or {}
    alerted_floor = prior_alert.get('setup_floor')
    alerted_ts = prior_alert.get('setup_floor_ts')
    prior_break = floor_breach(bars, alerted_floor, floor_ts=alerted_ts,
                              known=prior_alert.get('invalidated_at_ts')) if type(alerted_ts) is int else None
    current_bars = [bar for bar in bars if type(prior_break) is not int or bar['ts'] >= prior_break]
    current = intraday_structure(current_bars)
    evaluations = {}
    for lane, route in configured_routes.items():
        level, floor = route.get('level'), route.get('floor')
        floor_ts = route.get('floor_ts')
        quoted_floor = number(floor) and floor > 0
        latest_break = floor_breach(current_bars, floor, floor_ts=floor_ts)
        if latest_break is not None:
            active = [bar for bar in current_bars if bar['ts'] >= latest_break]
            observed = intraday_structure(active)
        else:
            observed = current
        # A stale or off-window reference may still be displayed for research;
        # it cannot confirm a setup without a fresh independently formed pivot.
        floor_current = (quoted_floor and type(floor_ts) is int and bars[0]['ts'] <= floor_ts <= last['ts']
                         and latest_break is None and (type(prior_break) is not int or floor_ts >= prior_break))
        early = snapshot['fresh'] and observed.get('early_recovery_observed') is True
        structure = early and observed.get('quality') is True
        breakout = bool(floor_current and number(level) and price > level)
        zone = route.get('zone')
        hold = bool(floor_current and isinstance(zone, list) and len(zone) == 2
                    and all(number(value) for value in zone) and zone[0] <= price <= zone[1])
        evaluations[lane] = {'old_setup_invalidated': latest_break is not None,
                             'breakout_observed': breakout, 'hold_observed': hold,
                             'old_level_available': floor_current, 'structure': observed,
                             'early': early, 'confirmed': structure}
    if not evaluations:
        evaluations['current'] = {'early': snapshot['fresh'] and current.get('early_recovery_observed') is True,
                                  'confirmed': snapshot['fresh'] and current.get('quality') is True,
                                  'structure': current}
    early = any(route['early'] for route in evaluations.values())
    # Current confirmation uses fresh, complete price structure, even if a
    # previous setup failed. No pre-breach bars contribute to that route.
    confirmed = any(route['confirmed'] for route in evaluations.values())
    best = max(evaluations.values(), key=lambda route: (route['confirmed'], route['early']))
    structure = best['structure']
    trigger = eligible and confirmed
    invalidated = type(prior_break) is int or any(route.get('old_setup_invalidated') for route in evaluations.values())
    status = ('DEGIRO-VERIFY-NOW' if trigger else 'EARLY-RECOVERY-WATCH' if early and not confirmed
              else 'STRUCTURE-OBSERVED' if confirmed else 'STALE-PROVIDER' if not snapshot['fresh']
              else 'SETUP-INVALIDATED' if invalidated else 'WATCH')
    return {**result, 'status': status, 'route_evidence': evaluations,
            'structure_available': structure['available'], 'early_turn_observed': early,
            'intraday_hold_confirmed': confirmed, 'prealert_trigger_observed': trigger,
            'breakout_observed': any(route.get('breakout_observed') for route in evaluations.values()),
            'hold_observed': confirmed, 'day_low': structure.get('recovery_low'),
            'route_2_break_above': structure.get('first_rebound_high') if early else None,
            'rebound_from_day_low_pct': structure.get('rebound_pct'),
            'previous_alert_invalidated_at_ts': prior_break if snapshot['fresh'] else None,
            'setup_floor': structure.get('recovery_low'), 'setup_floor_ts': structure.get('recovery_low_ts'),
            'setup_id': (f"{structure['recovery_low_ts']}|{structure['recovery_low']}" if early else None),
            'company_event': (item.get('discovery_evidence', {}).get('deep') or {}).get('company_event'),
            'execution_blocks': ['BROKER-BID-ASK-NOT-VERIFIED', 'NET-MONEY-RR-NOT-VERIFIED', 'NEWS-EVENT-PORTFOLIO-FIT-PENDING']}


def main():
    report = build_routes(read_report(SRC), read_report(GATE), now=datetime.now(timezone.utc))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2))
    print(f"US_LIVE_ROUTES: tickers={len(report['rows'])}")


if __name__ == '__main__':
    main()
