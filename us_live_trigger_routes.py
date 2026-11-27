#!/usr/bin/env python3
"""Build and evaluate independent live recovery routes for US PRE-ALERT."""
import json
from datetime import datetime, timezone
from pathlib import Path

from eu_entry_net import age_seconds
from recovery_price_evidence import breakout_stage, level_observations, resistance_room
from us_auto_prealert_handoff import DISABLED, read_report
from us_intraday_recovery import intraday_structure
from us_momentum_recovery_discovery import discovery_rebound_allowed
from us_yahoo_bars import MAX_MINUTE_AGE, MINUTE_BAR_SOURCE, number
from us_recovery_continuity import (DEFERRED, EXPIRED, REJECTED, REVOKED, UNAVAILABLE,
                                   active_qualification, fresh_evidence, reconcile)

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


def route_levels(lane, evidence):
    if lane == 'fast':
        shape = evidence.get('intraday_structure') or {}
        return {'level': shape.get('first_rebound_high'), 'floor': shape.get('recovery_low'),
                'floor_ts': shape.get('recovery_low_ts')}
    return {'floor': evidence.get('historical_invalidation_reference_usd')}


def follow_reason(lane, record, now):
    evidence = record.get('evidence')
    if not fresh_evidence(evidence, record.get('evidence_observed_utc'), now):
        return None
    if lane == 'fast':
        transient_rejection = (record.get('retirement_reason') == REJECTED
                               and record.get('retirement_detail') == 'discovery_gate_rejected')
        drawdown, trough = evidence.get('recent_drawdown_pct'), evidence.get('recent_20d_trough_usd')
        if ((not record.get('qualification_retired') or transient_rejection)
                and number(drawdown) and drawdown <= -8 and number(trough) and trough > 0):
            return 'PRIOR_FAST_RECOVERY'
    elif (not record.get('qualification_retired') and evidence.get('early_turn') is True
          and evidence.get('weekly_structure_support') is True
          and number(evidence.get('historical_invalidation_reference_usd'))
          and evidence['historical_invalidation_reference_usd'] > 0):
        return 'DEEP_EARLY_TURN'
    return None


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
            else:
                count, space = item.get('bottom_signal_count'), item.get('space_to_first_overhead_pct')
                quality = (type(count) is int and count >= 4 and item.get('identity_status') == 'NAME_CONSISTENT_UNVERIFIED'
                           and number(space) and space >= 3)
            live_routes[lane] = {**route_levels(lane, item), 'qualification_utc': qualification['utc'],
                                 'level_observed_utc': item.get('observed_utc') or qualification['utc']}
            if quality or symbol in watchlist:
                qualified.append(lane)
        allow_requalification = not (disputed or symbol in silent or explicitly_revoked)
        follow_reasons = {}
        for lane, record in lanes.items():
            reason = follow_reason(lane, record, now)
            if reason is None or explicitly_revoked or disputed:
                continue
            follow_reasons[lane] = reason
            if lane not in qualified:
                stamp = record['evidence_observed_utc']
                route = live_routes.setdefault(lane, {**route_levels(lane, evidence[lane]),
                                                       'level_observed_utc': stamp})
                route.update(watch_evidence_utc=stamp, watch_reason=reason,
                             watch_last_bar_date=evidence[lane].get('last_bar_date'),
                             recheck_after_utc=record.get('observed_utc'),
                             watch_trough=evidence[lane].get('recent_20d_trough_usd'))
        # A never-promoted, current candidate can still be watched silently.
        recent_watch = any(record.get('status') in (DEFERRED, UNAVAILABLE) and not record.get('qualification_retired')
                           and fresh_evidence(record.get('evidence'), record.get('evidence_observed_utc'), now)
                           for record in lanes.values())
        if not (active or disputed or explicitly_revoked or recent_watch or follow_reasons):
            continue
        eligible = bool(qualified and allow_requalification)
        deep = lanes.get('deep', {})
        historical_resistance = ((deep.get('evidence') or {}).get('historical_first_overhead_reference_usd')
                                 if fresh_evidence(deep.get('evidence'), deep.get('evidence_observed_utc'), now) else None)
        lane_outcomes = dict((outcomes or {}).get(symbol, {}))
        for lane, record in lanes.items():
            if record.get('qualification') and not record.get('qualification_retired') and lane not in active:
                lane_outcomes[lane] = EXPIRED
        rows.append({'symbol': symbol, 'name': (evidence.get('fast') or evidence.get('deep') or {}).get('name'),
                     'observed_utc': max(record['observed_utc'] for record in lanes.values()),
                     'status': 'PRE-ALERT' if eligible else 'SILENT-FOLLOW',
                     'phone_notification_eligible': eligible, 'silent_follow': not eligible,
                     'notification_lanes': qualified if eligible else [], 'lane_outcomes': lane_outcomes,
                     'follow_reasons': follow_reasons, 'allow_requalification': allow_requalification,
                     'historical_first_overhead_reference_usd': historical_resistance,
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


def route_stamp(route):
    return route.get('qualification_utc') or route.get('watch_evidence_utc')


def monitor_recovery(item, snapshot, *, prior_alert=None):
    """Evaluate live evidence and discard old setups upon a breach or time gap."""
    if snapshot['symbol'] != item['symbol']:
        raise ValueError('WATCH_SNAPSHOT_SYMBOL_MISMATCH')
    bars = snapshot['bars']
    last = snapshot['latest_completed_bar']
    price = last['close']
    last_stamp = datetime.fromtimestamp(last['ts'], timezone.utc)
    closed_at = datetime.fromtimestamp(last['ts'] + 60, timezone.utc)
    eligible = item.get('phone_notification_eligible') is True
    recheck = (item.get('allow_requalification') is True
               and not (item.get('identity_disputed') or item.get('explicitly_revoked'))
               and snapshot['fresh'] and snapshot.get('latest_completed_minute_missing') is False
               and snapshot['source'] == MINUTE_BAR_SOURCE
               and number(snapshot['bar_age_seconds']) and 60 <= snapshot['bar_age_seconds'] <= MAX_MINUTE_AGE)
    observed_at = (datetime.fromtimestamp(last['ts'] + snapshot['bar_age_seconds'], timezone.utc)
                   if recheck else None)
    result = {'symbol': item['symbol'], 'market': 'US', 'watch_type': 'AUTO-US-DISCOVERY',
              'phone_notification_eligible': eligible, 'provider_quote': price,
              'provider_quote_utc': last_stamp.isoformat(),
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
    approved = item.get('notification_lanes')
    renewed = set()
    for lane, route in configured_routes.items():
        level, floor = route.get('level'), route.get('floor')
        floor_ts = route.get('floor_ts')
        quoted_floor = number(floor) and floor > 0
        prior_lane = (prior_alert.get('lanes') or {}).get(lane) or {}
        evidence_stamp = route_stamp(route)
        known = (prior_lane.get('breach_ts') if prior_lane.get('qualification_utc') == evidence_stamp else None)
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
        watch_stamp = route.get('watch_evidence_utc')
        trough = route.get('watch_trough')
        rebound_allowed = lane == 'deep' or (number(trough) and trough > 0
                                             and discovery_rebound_allowed((price / trough - 1) * 100, early))
        since_scan = age_seconds(route.get('recheck_after_utc'), closed_at)
        requalified = (recheck and early and lane in ('fast', 'deep') and lane not in (approved or [])
                       and route.get('watch_reason')
                       and rebound_allowed and since_scan is not None and since_scan > 0
                       and fresh_evidence({'last_bar_date': route.get('watch_last_bar_date')}, watch_stamp, observed_at))
        qualification = route.get('qualification_utc')
        if requalified:
            renewed.add(lane)
            qualification = last_stamp.isoformat()
            # Deferred deep evidence can support attention only. This path
            # does not replace its identity, selection or execution checks.
            structure = structure and lane == 'fast'
        level_age = age_seconds(route.get('level_observed_utc'), last_stamp)
        proof = (level_observations(current_bars, level, max(floor_ts, last['ts'] - int(level_age)))
                 if snapshot['fresh'] and floor_current and level_age is not None and level_age > 0 else {})
        evaluations[lane] = {'old_setup_invalidated': latest_break is not None,
                             'breach_ts': latest_break if snapshot['fresh'] else None,
                             'qualification_utc': qualification,
                             'breach_reference_utc': evidence_stamp,
                             'requalification_context_utc': watch_stamp if requalified else None,
                             'requalification_last_bar_date': route.get('watch_last_bar_date') if requalified else None,
                             'breakout_evidence': proof, 'breakout_observed': 'breakout' in proof,
                             'hold_observed': 'hold' in proof, 'retest_observed': 'retest' in proof,
                             'old_level_available': floor_current, 'structure': observed,
                             'early': early, 'confirmed': structure}
    if not evaluations:
        evaluations['current'] = {'early': snapshot['fresh'] and current.get('early_recovery_observed') is True,
                                  'confirmed': snapshot['fresh'] and current.get('quality') is True,
                                  'structure': current}
    actionable = [route for lane, route in evaluations.items()
                  if lane in renewed or (eligible and (approved is None or lane in approved))]
    eligible = eligible or bool(renewed)
    early = any(route['early'] for route in (actionable if eligible else evaluations.values()))
    # Current confirmation uses fresh, complete price structure, even if a
    # previous setup failed. No pre-breach bars contribute to that route.
    confirmed = any(route['confirmed'] for route in (actionable if eligible else evaluations.values()))
    best = max(actionable or evaluations.values(),
               key=lambda route: (route['confirmed'], route['early'], len(route.get('breakout_evidence', {}))))
    structure = best['structure']
    proof = best.get('breakout_evidence', {}) if best['confirmed'] else {}
    stage = breakout_stage(proof, last['ts'], price)
    trigger = eligible and confirmed
    invalidated = type(prior_break) is int or any(route.get('old_setup_invalidated') for route in evaluations.values())
    status = ('DEGIRO-VERIFY-NOW' if trigger else 'EARLY-RECOVERY-WATCH' if early and not confirmed
              else 'STRUCTURE-OBSERVED' if confirmed else 'STALE-PROVIDER' if not snapshot['fresh']
              else 'SETUP-INVALIDATED' if invalidated else 'WATCH')
    return {**result, 'status': status, 'route_evidence': evaluations,
            'phone_notification_eligible': eligible, 'requalified_lanes': sorted(renewed),
            'follow_reasons': item.get('follow_reasons', {}),
            'structure_available': structure['available'], 'early_turn_observed': early,
            'intraday_hold_confirmed': confirmed, 'prealert_trigger_observed': trigger,
            'breakout_evidence': proof, 'breakout_observed': stage is not None,
            'hold_observed': stage in ('hold', 'retest'), 'retest_observed': stage == 'retest',
            'day_low': structure.get('recovery_low'),
            'route_2_break_above': proof.get('level') if stage else None,
            'resistance_room': resistance_room(
                item.get('historical_first_overhead_reference_usd'),
                price if snapshot['fresh'] else None, price_basis='PROVIDER_COMPLETED_MINUTE'),
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
            stamp = route_stamp(route)
            if stamp is None:
                continue
            prior = previous.get(symbol, {}).get(lane, {})
            observed = fresh.get(symbol, {}).get(lane, {})
            breaches = [record['breach_ts'] for record in (prior, observed)
                        if record.get('breach_reference_utc', record.get('qualification_utc')) == stamp
                        and type(record.get('breach_ts')) is int]
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
