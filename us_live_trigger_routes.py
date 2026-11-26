#!/usr/bin/env python3
"""Build and evaluate independent live recovery routes for US PRE-ALERT."""
import json
from datetime import datetime, timezone
from pathlib import Path

from eu_entry_net import age_seconds
from us_auto_prealert_handoff import DISABLED, read_report
from us_intraday_recovery import intraday_structure
from us_yahoo_bars import number
from us_recovery_continuity import (DEFERRED, EVIDENCE_MAX_AGE, EXPIRED, REVOKED, UNAVAILABLE,
                                   active_qualification, reconcile)

SRC = Path('reports/us_auto_prealert_candidates.json')
OUT = Path('reports/us_live_trigger_routes.json')
GATE = Path('config/notification_quality_gate.json')


def build_routes(handoff, gate, *, now, previous=None, failed_batches=(), fast_failed=False):
    registry, outcomes = reconcile(previous or {}, handoff.get('lane_events', {}), now=now,
                                   revoked=set(gate.get('auto_us_revoked', [])),
                                   failed_batches=failed_batches, fast_failed=fast_failed)
    return {'generated_utc': now.isoformat(), 'scope': 'US recovery research and live monitoring',
            'lane_registry': registry, 'scan_outcomes': outcomes,
            'rows': route_rows(registry, gate, now=now, outcomes=outcomes), **DISABLED}


def route_rows(registry, gate, *, now, outcomes=None):
    watchlist = set(gate.get('auto_us_notify_watchlist', [])) | {'GEHC'}
    silent = set(gate.get('auto_us_silent_follow', []))
    revoked = set(gate.get('auto_us_revoked', []))
    rows = []
    for symbol, lanes in registry.items():
        evidence = {lane: record['evidence'] for lane, record in lanes.items() if record.get('evidence')}
        active = {lane: record['qualification'] for lane, record in lanes.items() if active_qualification(record, now)}
        disputed = any(record.get('identity_disputed') is True for record in lanes.values())
        revoked_ages = [age for record in lanes.values() if record.get('retirement_reason') == REVOKED
                        and not record.get('identity_disputed')
                        if (age := age_seconds(record.get('retired_utc'), now)) is not None]
        requalified = any(age_seconds(item['utc'], now) < min(revoked_ages) for item in active.values()) if revoked_ages else False
        explicitly_revoked = symbol in revoked or bool(revoked_ages and not requalified)
        qualified = []
        live_routes = {}
        for lane, qualification in active.items():
            item = qualification['evidence'] or {}
            shape = item.get('intraday_structure') or {}
            if lane == 'fast':
                drawdown = item.get('recent_drawdown_pct')
                quality = shape.get('early_recovery_observed') is True and number(drawdown) and drawdown <= -8
                levels = {'level': shape.get('first_rebound_high'), 'floor': shape.get('recovery_low'),
                          'floor_ts': shape.get('recovery_low_ts')}
            else:
                count, space = item.get('bottom_signal_count'), item.get('space_to_first_overhead_pct')
                quality = (type(count) is int and count >= 4 and item.get('identity_status') == 'NAME_CONSISTENT_UNVERIFIED'
                           and number(space) and space >= 3)
                zone = (item.get('historical_overhead_zones') or [{}])[0]
                levels = {'level': zone.get('low_usd'), 'zone': [zone.get('low_usd'), zone.get('high_usd')],
                          'floor': item.get('historical_invalidation_reference_usd')}
            live_routes[lane] = {**levels, 'qualification_utc': qualification['utc']}
            if quality or symbol in watchlist:
                qualified.append(lane)
        # A never-promoted, current candidate can still be watched silently.
        evidence_ages = {lane: age_seconds(record.get('evidence_observed_utc'), now) for lane, record in lanes.items()}
        recent_watch = any(record.get('status') in (DEFERRED, UNAVAILABLE) and not record.get('qualification_retired')
                           and evidence_ages[lane] is not None and 0 <= evidence_ages[lane] <= EVIDENCE_MAX_AGE
                           for lane, record in lanes.items())
        if not active and not disputed and not explicitly_revoked and not recent_watch:
            continue
        eligible = bool(qualified and not disputed and symbol not in silent and not explicitly_revoked)
        lane_outcomes = dict((outcomes or {}).get(symbol, {}))
        for lane, record in lanes.items():
            if record.get('qualification') and not record.get('qualification_retired') and lane not in active:
                lane_outcomes[lane] = EXPIRED
        rows.append({'symbol': symbol, 'name': (evidence.get('fast') or evidence.get('deep') or {}).get('name'),
                     'observed_utc': max(record['observed_utc'] for record in lanes.values()),
                     'status': 'PRE-ALERT' if eligible else 'SILENT-FOLLOW',
                     'phone_notification_eligible': eligible, 'silent_follow': not eligible,
                     'notification_lanes': qualified if eligible else [], 'lane_outcomes': lane_outcomes,
                     'identity_disputed': disputed, 'explicitly_revoked': explicitly_revoked,
                     'discovery_evidence': evidence, 'live_routes': live_routes,
                     'route_is_execution_signal': False, **DISABLED})
    return rows


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
              'contiguous_completed_bars': len(bars),
              'latest_completed_minute_missing': snapshot.get('latest_completed_minute_missing'), **DISABLED}
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
        prior_lane = (prior_alert.get('lanes') or {}).get(lane) or {}
        known = (prior_lane.get('breach_ts') if prior_lane.get('qualification_utc') == route.get('qualification_utc') else None)
        latest_break = floor_breach(current_bars, floor, floor_ts=floor_ts, known=known)
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
                             'breach_ts': latest_break if snapshot['fresh'] else None,
                             'qualification_utc': route.get('qualification_utc'),
                             'breakout_observed': breakout, 'hold_observed': hold,
                             'old_level_available': floor_current, 'structure': observed,
                             'early': early, 'confirmed': structure}
    if not evaluations:
        evaluations['current'] = {'early': snapshot['fresh'] and current.get('early_recovery_observed') is True,
                                  'confirmed': snapshot['fresh'] and current.get('quality') is True,
                                  'structure': current}
    approved = item.get('notification_lanes')
    actionable = [route for lane, route in evaluations.items() if approved is None or lane in approved]
    early = any(route['early'] for route in (actionable if eligible else evaluations.values()))
    # Current confirmation uses fresh, complete price structure, even if a
    # previous setup failed. No pre-breach bars contribute to that route.
    confirmed = any(route['confirmed'] for route in (actionable if eligible else evaluations.values()))
    best = max(actionable or evaluations.values(), key=lambda route: (route['confirmed'], route['early']))
    structure = best['structure']
    trigger = eligible and confirmed
    invalidated = type(prior_break) is int or any(route.get('old_setup_invalidated') for route in evaluations.values())
    status = ('DEGIRO-VERIFY-NOW' if trigger else 'EARLY-RECOVERY-WATCH' if early and not confirmed
              else 'STRUCTURE-OBSERVED' if confirmed else 'STALE-PROVIDER' if not snapshot['fresh']
              else 'SETUP-INVALIDATED' if invalidated else 'WATCH')
    return {**result, 'status': status, 'route_evidence': evaluations,
            'structure_available': structure['available'], 'early_turn_observed': early,
            'intraday_hold_confirmed': confirmed, 'prealert_trigger_observed': trigger,
            'breakout_observed': any(route.get('breakout_observed') and route['confirmed']
                                     for route in (actionable if eligible else evaluations.values())),
            'hold_observed': confirmed, 'day_low': structure.get('recovery_low'),
            'route_2_break_above': structure.get('first_rebound_high') if early else None,
            'rebound_from_day_low_pct': structure.get('rebound_pct'),
            'previous_alert_invalidated_at_ts': prior_break if snapshot['fresh'] else None,
            'setup_floor': structure.get('recovery_low'), 'setup_floor_ts': structure.get('recovery_low_ts'),
            'alert_qualification_utc': [view['qualification_utc'] for view in actionable
                                        if view.get('qualification_utc') and (view['confirmed'] if confirmed else view['early'])],
            'setup_id': (f"{structure['recovery_low_ts']}|{structure['recovery_low']}" if early else None),
            'company_event': (item.get('discovery_evidence', {}).get('deep') or {}).get('company_event'),
            'execution_blocks': ['BROKER-BID-ASK-NOT-VERIFIED', 'NET-MONEY-RR-NOT-VERIFIED', 'NEWS-EVENT-PORTFOLIO-FIT-PENDING']}


def persist_lane_breaches(routes, entries, previous):
    """Keep a breach only for the exact qualification still in the US store."""
    retained = {}
    fresh = {row['symbol']: row.get('route_evidence', {}) for row in entries
             if row.get('market') == 'US' and row.get('provider_freshness_pass') is True}
    for item in routes:
        symbol = item['symbol']
        for lane, route in item.get('live_routes', {}).items():
            stamp = route['qualification_utc']
            prior = previous.get(symbol, {}).get(lane, {})
            observed = fresh.get(symbol, {}).get(lane, {})
            breaches = [record['breach_ts'] for record in (prior, observed)
                        if record.get('qualification_utc') == stamp and type(record.get('breach_ts')) is int]
            if breaches:
                retained.setdefault(symbol, {})[lane] = {'qualification_utc': stamp, 'breach_ts': max(breaches)}
    return retained


def main():
    report = build_routes(read_report(SRC), read_report(GATE), now=datetime.now(timezone.utc))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2))
    print(f"US_LIVE_ROUTES: tickers={len(report['rows'])}")


if __name__ == '__main__':
    main()
