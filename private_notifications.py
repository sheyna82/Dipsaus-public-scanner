"""Selective phase upgrades and profit decisions. Reserve before sending; no duplicate retries."""
import os
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from dipsaus_breakout_distance import historical_resistance_context, message_context
from recovery_price_evidence import breakout_stage
import urllib.request

from eu_entry_net import age_seconds
from us_recovery_continuity import EVIDENCE_MAX_AGE, fresh_evidence
from us_yahoo_bars import MAX_MINUTE_AGE, MINUTE_BAR_SOURCE, number

# Provider symbols are not always searchable verbatim in DEGIRO.
# Display verified issuer names and ISINs; never change quote-feed symbols.
BROKER_IDENTIFIERS = {
    'MC.PA': ('LVMH Moet Hennessy Louis Vuitton', 'FR0000121014'),
    'STLAM.MI': ('Stellantis N.V.', 'NL00150001Q9'),
    'KER.PA': ('Kering SA', 'FR0000121485'),
    'FER.MC': ('Ferrovial SE', 'NL0015001FS8'),
}

def broker_search_hint(symbol):
    item = BROKER_IDENTIFIERS.get(symbol)
    if not item:
        return ''
    return 'DEGIRO zoeken: ' + item[0] + ' | ISIN ' + item[1] + '\\n'

RANK = {'BOTTOM-RECOVERY': 1, 'BREAKOUT-SEEN': 2, 'CURRENT-RECOVERY-CONFIRMED': 2,
        'BREAKOUT-HOLD-RETEST': 3, 'EXECUTION-NEAR': 4}


def phase(row):
    if row.get('market') == 'US':
        if row.get('intraday_hold_confirmed') is not True:
            return 'BOTTOM-RECOVERY'
        bar = row.get('completed_minute_bar') or {}
        stage = breakout_stage(row.get('breakout_evidence'), bar.get('ts'), row.get('provider_quote'))
        if stage == 'retest':
            return 'BREAKOUT-HOLD-RETEST'
        return 'BREAKOUT-SEEN' if stage else 'CURRENT-RECOVERY-CONFIRMED'
    text = ' '.join(str(row.get(k, '')) for k in ('status', 'triggered_route', 'trigger_route', 'route', 'setup_phase')).upper()
    yes = lambda *keys: any(bool(row.get(k)) for k in keys)
    breakout = yes('breakout_observed', 'breakout_seen', 'breakout_confirmed') or 'BREAKOUT' in text
    hold = yes('breakout_hold_observed', 'retest_hold_observed', 'hold_observed', 'higher_low_observed', 'recent_reclaim_observed')
    execution = yes('execution_near', 'buy_ready', 'execution_qualified') or any(x in text for x in ('BUY-READY', 'KOOPKLAAR', 'EXECUTION-NEAR', 'VERY-NEAR-BUY-READY'))
    if execution: return 'EXECUTION-NEAR'
    if breakout and hold: return 'BREAKOUT-HOLD-RETEST'
    if breakout: return 'BREAKOUT-SEEN'
    return 'BOTTOM-RECOVERY'


EXPIRED = 'expired_before_send'
AMBIGUOUS = {'reserved', 'uncertain'}


def uses_daily_budget(record):
    # Keep old records without a delivery field conservative.
    return not isinstance(record, dict) or record.get('delivery') not in (EXPIRED, 'rejected')


def archive_expired_attempt(signals, key, record):
    signals[f"{key}|EXPIRED|{record.get('notified_utc', 'unknown')}"] = record



def confirmed_ledger_record(signals, key, now):
    record = signals.get(key, {})
    if record.get('delivery') != EXPIRED:
        return record
    # Older scanner versions could replace a delivered phase with a failed
    # promotion. Recover the prior phase from its existing audit history.
    prefix = key.removesuffix('|PHASE') + '|HISTORY|'
    history = [item for audit_key, item in signals.items()
               if audit_key.startswith(prefix) and isinstance(item, dict) and item.get('delivery') != EXPIRED]

    def age(item):
        value = age_seconds(item.get('notified_utc'), now)
        return (value if value is not None and value >= 0 else float('inf'), -RANK.get(item.get('phase'), 0))
    return min(history, key=age, default={})

def current_minute(row, now):
    age = age_seconds(row.get('provider_quote_utc'), now)
    if (row.get('provider_source') != MINUTE_BAR_SOURCE or age is None or not 0 <= age <= MAX_MINUTE_AGE
            or row.get('provider_freshness_pass') is not True or row.get('latest_completed_minute_missing') is not False):
        return False
    bar = row.get('completed_minute_bar')
    price = row.get('provider_quote')
    if (not isinstance(bar, dict) or not number(price) or price <= 0
            or not number(bar.get('close')) or bar['close'] != price):
        return False
    stamp = datetime.fromisoformat(row['provider_quote_utc'].replace('Z', '+00:00')).timestamp()
    return type(bar.get('ts')) is int and bar['ts'] % 60 == 0 and stamp == bar['ts']


def current_automatic_structures(row, now):
    declared = row.get('alert_qualification_utc')
    routes = row.get('route_evidence')
    if not isinstance(declared, list) or not isinstance(routes, dict):
        return []
    stamps = {stamp for stamp in declared if (age := age_seconds(stamp, now)) is not None and 0 <= age <= EVIDENCE_MAX_AGE}
    status = row.get('status')
    if status not in ('EARLY-RECOVERY-WATCH', 'DEGIRO-VERIFY-NOW'):
        return []
    stage = 'early' if status == 'EARLY-RECOVERY-WATCH' else 'confirmed'
    structures = []
    for lane, route in routes.items():
        if lane not in ('fast', 'deep') or not isinstance(route, dict):
            continue
        stamp, shape = route.get('qualification_utc'), route.get('structure')
        if (not isinstance(stamp, str) or stamp not in stamps or route.get(stage) is not True
                or not isinstance(shape, dict) or shape.get('early_recovery_observed') is not True
                or (stage == 'confirmed' and shape.get('quality') is not True)):
            continue
        context_utc = route.get('requalification_context_utc')
        if context_utc is not None and not fresh_evidence(
                {'last_bar_date': route.get('requalification_last_bar_date')}, context_utc, now):
            continue
        if route.get('old_setup_invalidated') is True:
            breach, new_floor = route.get('breach_ts'), shape.get('recovery_low_ts')
            if type(breach) is not int or type(new_floor) is not int or new_floor < breach:
                continue
        structures.append(shape)
    return structures


def early_priority(row, now):
    def quality(shape):
        floor, higher = shape.get('recovery_low'), shape.get('higher_low')
        spacing = (higher - floor) / floor if number(floor) and floor > 0 and number(higher) else 0
        efficiency = shape.get('path_efficiency')
        return (shape.get('reclaim_observed') is True, spacing, efficiency if number(efficiency) else 0)

    strength = max((quality(shape) for shape in current_automatic_structures(row, now)), default=(False, 0, 0))
    age = age_seconds(row.get('provider_quote_utc'), now)
    return (*(-value for value in strength), age if age is not None else float('inf'), row.get('symbol') or '')


def reserve_send(store, state, key, record, symbol, body, sender=None, *, preflight=None):
    """Persist delivery outcomes; never silently treat a failed push as sent.

    An ambiguous network outcome is intentionally NOT automatically retried:
    the ntfy server may have accepted it before the connection failed.
    """
    import re
    from urllib.error import HTTPError

    topic = None
    if sender is None:
        topic = os.environ.get('NTFY_TOPIC', '')
        if not topic:
            raise RuntimeError('NOTIFICATION_SECRET_NOT_CONFIGURED')
        if not re.fullmatch(r'[A-Za-z0-9_-]+', topic):
            raise RuntimeError('NOTIFICATION_TOPIC_INVALID')

    signals = state['signals']
    previous = signals.get(key)
    if previous and previous.get('delivery') == EXPIRED:
        archive_expired_attempt(signals, key, previous)
    record['delivery'] = 'reserved'
    signals[key] = record
    store.save(state)
    if preflight is not None and not preflight():
        record['delivery'] = EXPIRED
        if previous and previous.get('delivery') != EXPIRED:
            archive_expired_attempt(signals, key, record)
            signals[key] = previous
        store.save(state)
        return False
    try:
        if sender:
            sender(symbol, body)
        else:
            req = urllib.request.Request(
                'https://ntfy.sh/' + topic, data=body.encode(), method='POST',
                headers={'Title': 'DIPSAUS - ' + symbol, 'Priority': '5'})
            with urllib.request.urlopen(req, timeout=15) as response:
                if not 200 <= response.status < 300:
                    raise RuntimeError('NOTIFICATION_DELIVERY_UNCERTAIN')
    except HTTPError as exc:
        # Timeouts and server-side errors can be returned after acceptance.
        record['delivery'] = 'rejected' if 400 <= exc.code < 500 and exc.code != 408 else 'uncertain'
        record['delivery_error'] = 'HTTP_' + str(exc.code)
        store.save(state)
        if record['delivery'] == 'uncertain':
            raise RuntimeError('NOTIFICATION_DELIVERY_UNCERTAIN') from None
        raise RuntimeError('NOTIFICATION_HTTP_REJECTED_' + str(exc.code)) from None
    except Exception:
        record['delivery'] = 'uncertain'
        record['delivery_error'] = 'NETWORK_OR_SENDER_ERROR'
        store.save(state)
        if sender is not None:
            raise  # Preserve injected sender exceptions for regression tests.
        raise RuntimeError('NOTIFICATION_DELIVERY_UNCERTAIN') from None
    record['delivery'] = 'sent'
    record.pop('delivery_error', None)
    store.save(state)
    return True


def notify(store, state, entries, exits, sender=None):
    store.require_exclusive_sender()
    east = ZoneInfo('America/New_York')
    signals = state.setdefault('signals', {})
    round_time = datetime.now(timezone.utc)
    early_rows = []
    other_rows = []
    for entry in entries:
        if entry.get('watch_type') == 'AUTO-US-DISCOVERY' and entry.get('status') == 'EARLY-RECOVERY-WATCH':
            early_rows.append(entry)
        else:
            other_rows.append(entry)

    for row in other_rows + sorted(early_rows, key=lambda item: early_priority(item, round_time)):
        if row.get('market') != 'US' or row.get('watch_type') not in ('AUTO-US-DISCOVERY', 'MANUAL-US-RECOVERY'):
            continue
        symbol = row.get('symbol')
        if not symbol:
            continue
        now = datetime.now(timezone.utc)
        day = now.astimezone(east).date().isoformat()
        automatic = row['watch_type'] == 'AUTO-US-DISCOVERY'

        def still_current():
            checked = datetime.now(timezone.utc)
            return (checked.astimezone(east).date().isoformat() == day and current_minute(row, checked)
                    and (not automatic or bool(current_automatic_structures(row, checked))))

        key = f'ENTRY|US|{symbol}|PHASE'
        previous = confirmed_ledger_record(signals, key, now)
        breach = row.get('previous_alert_invalidated_at_ts')
        if (current_minute(row, now) and previous and type(breach) is int
                and breach > (previous.get('invalidated_at_ts') or 0)):
            previous['invalidated_at_ts'] = breach
            store.save(state)
        if (row.get('status') == 'SETUP-INVALIDATED'
                or not (still_current() and row.get('phone_notification_eligible') and row.get('structure_available'))):
            continue
        prior_day = previous.get('day')
        prior_age = age_seconds(previous.get('notified_utc'), now)
        if prior_day is None and prior_age is not None and prior_age >= 0:
            prior_day = (now - timedelta(seconds=prior_age)).astimezone(east).date().isoformat()
        early_key = f'US-EARLY|{symbol}|{day}'
        early_previous = signals.get(early_key, {})
        if (early_previous.get('delivery') in AMBIGUOUS
                or (prior_day in (None, day) and previous.get('delivery') in AMBIGUOUS)):
            continue
        if automatic and row.get('status') == 'EARLY-RECOVERY-WATCH' and row.get('early_turn_observed'):
            already = sum(1 for old_key, old_record in signals.items()
                          if old_key.startswith('US-EARLY|') and old_key.count('|') == 2
                          and old_key.endswith('|' + day) and uses_daily_budget(old_record))
            if (not early_previous or early_previous.get('delivery') == EXPIRED) and already < 3 and prior_day != day:
                record = {'day': day, 'notification_schema_version': 16, 'notified_utc': now.isoformat()}
                body = (f'{symbol} VROEGE HERSTELKANS (ONDERZOEK)\n'
                        f'Voltooide minuutslotkoers {row.get("provider_quote")}, '
                        f'herstelbodem {row.get("day_low")}. Onderzoekswaarschuwing voor handmatige beoordeling. '
                        'Controleer DEGIRO bied/laat, structurele invalidatie, eerste weerstand, '
                        'nettowinst, netto R/R, kwartaalcijfers en portefeuilleruimte.'
                        + historical_resistance_context(row))
                reserve_send(store, state, early_key, record, symbol, body, sender, preflight=still_current)
            continue
        if not (row.get('prealert_trigger_observed') and row.get('intraday_hold_confirmed')):
            continue
        current_phase = phase(row)
        if current_phase == 'BOTTOM-RECOVERY':
            continue
        floor_ts = row.get('setup_floor_ts')
        has_new_setup = bool(row.get('setup_id') and row['setup_id'] != previous.get('setup_id')
                             and type(floor_ts) is int)
        new_after_breach = (has_new_setup and type(previous.get('invalidated_at_ts')) is int
                            and floor_ts >= previous['invalidated_at_ts'])
        new_trading_day = (has_new_setup and prior_day is not None and prior_day < day
                           and datetime.fromtimestamp(floor_ts, timezone.utc).astimezone(east).date().isoformat() == day)
        attempts_today = previous.get('confirmed_attempts_today', 1) if prior_day == day else 0
        if previous.get('delivery') == 'rejected':
            attempts_today = max(0, attempts_today - 1)
        rearmed = new_trading_day or (new_after_breach and attempts_today < 2
                                     and previous.get('delivery') not in AMBIGUOUS)
        if not rearmed and RANK[current_phase] <= RANK.get(previous.get('phase'), 0):
            continue
        record = {'phase': current_phase, 'day': day, 'notification_schema_version': 16,
                  'notified_utc': now.isoformat(), 'setup_id': row.get('setup_id'),
                  'setup_floor': row.get('setup_floor'), 'setup_floor_ts': floor_ts,
                  'confirmed_attempts_today': attempts_today + 1}
        body = (f'{symbol} {current_phase}\nVoltooide provider-minuutslotkoers {row.get("provider_quote")}. '
                'Handmatige beoordeling vereist. Controleer DEGIRO bied/laat, invalidatie, eerste weerstand, '
                'werkelijke kosten, nettowinst, netto R/R, nieuws, kwartaalcijfers en portefeuilleruimte.')
        if current_phase in ('BREAKOUT-SEEN', 'BREAKOUT-HOLD-RETEST'):
            body += message_context({**row, 'route_2_break_above': row['breakout_evidence']['level']})
        body += historical_resistance_context(row)
        if previous:
            archive_id = previous.get('notified_utc', 'legacy')
            signals[f'ENTRY|US|{symbol}|HISTORY|{archive_id}'] = dict(previous)
        reserve_send(store, state, key, record, symbol, body, sender, preflight=still_current)
    for row in exits:
        symbol = row.get('symbol', 'UNKNOWN'); key = f'EXIT|{symbol}|STATE'
        prev = state['signals'].get(key, {})
        if not row.get('profit_alert'):
            if prev.get('active'):
                # Preserve the last sent state across brief quote/zone fluctuations.
                state['signals'][key] = dict(prev, active=False); store.save(state)
            continue
        reason = row.get('alert_reason') or 'DECISION-ZONE'; decision = row.get('decision') or 'WINSTCHECK'
        sid = f'{reason}|{decision}'
        today = datetime.now(timezone.utc).date().isoformat()
        # One ordinary decision-zone push per symbol/state/day even if the alert
        # temporarily clears. A materially different reason remains actionable.
        if prev.get('state_id') == sid and (
                prev.get('active') or prev.get('day') == today or
                str(prev.get('notified_utc', ''))[:10] == today):
            continue
        record = {'active': True, 'state_id': sid, 'day': today,
                  'notification_schema_version': 13,
                  'notified_utc': datetime.now(timezone.utc).isoformat()}
        # A decision-zone touch does not establish profit versus cost basis.
        # Keep deterioration/crash warnings urgent even when below purchase price.
        protective = reason in (
            'FAST-CRASH-OVERRIDE', 'CONFIRMED-RECOVERY-STRUCTURE-DETERIORATION',
            'MATERIAL-BREAKOUT-GIVEBACK', 'FIRST-FRICTION-REJECTION',
        )
        if protective:
            headline = 'BESCHERMINGSCHECK NU'
        elif reason in ('FIRST-DECISION-ZONE', 'EXIT-REBOUND-BROKER-CHECK'):
            headline = 'KOERSZONECHECK - GEEN WINSTBEVESTIGING'
        else:
            headline = 'WEERSTANDSCHECK - WINST NIET BEVESTIGD'
        body = (f'{symbol}: {headline}\nReason: {reason}\n'
                f'Provider quote: {row.get("provider_quote")}\n'
                'Geen automatische verkoop. Controleer actuele DEGIRO bied/laat, '
                'GAK, herstelstructuur en momentum; providerkoers is geen uitvoeringskoers.')
        reserve_send(store, state, key, record, symbol, body, sender)


def release_declined_capacity(store, state, declines, now):
    """Apply explicit operator decisions to exact delivered research reservations."""
    if not isinstance(declines, (list, tuple)):
        return
    changed = False
    for decision in declines:
        if not isinstance(decision, dict):
            continue
        key = decision.get('reservation_key')
        parts = key.split('|') if isinstance(key, str) else []
        if len(parts) != 4 or parts[0] != 'EU-RESEARCH' or parts[2] != 'FINANCIAL_ENTRY_CONFIRMED':
            continue
        record = state['signals'].get(key)
        if (not isinstance(record, dict) or record.get('delivery') != 'sent' or record.get('day') != parts[3]
                or record.get('capacity_released_utc') or not isinstance(record.get('capacity'), dict)
                or record['capacity'].get('status') != 'CAPACITY_VERIFIED'
                or decision.get('notified_utc') != record.get('notified_utc')):
            continue
        decided = decision.get('decided_utc')
        age = age_seconds(decided, now)
        notified_age = age_seconds(record.get('notified_utc'), now)
        if age is not None and notified_age is not None and 0 <= age <= notified_age:
            record['capacity_released_utc'] = decided
            changed = True
    if changed:
        store.save(state)

def notify_eu_research(store, state, report, holdings, sender=None, *, evidence=None,
                       reviewer_pin=None, clock=None, positions=None, capacity_declines=()):
    """Re-evaluate EU stages and reserve every attempt in existing private history."""
    from collections import Counter
    from dipsaus_eu_freshness import classify_eu_report
    from eu_entry_net import (EARLY_RECOVERY, DEGIRO_VERIFICATION, FINANCIAL_ENTRY_CONFIRMED,
                              PHASE_RANK, assess_report, evaluate_entry, recovery_phase)

    if clock is None:
        clock = lambda: datetime.now(timezone.utc)
    now = clock()
    phase_counts = dict.fromkeys(PHASE_RANK, 0)
    reasons = Counter()
    summary = {'evaluated_utc': now.isoformat(),
               'phase_counts': phase_counts, 'reason_counts': reasons, 'financial_results': []}
    state['latest_eu_entry_evaluation'] = summary
    evidence = evidence if isinstance(evidence, dict) else {}
    priority_watch = {'KER.PA', 'FER.MC', 'SU.PA', 'ANTO.L'}
    signals = state.setdefault('signals', {})
    release_declined_capacity(store, state, capacity_declines, now)
    day = now.astimezone(ZoneInfo('Europe/Amsterdam')).date().isoformat()
    previous_rank = {}
    ambiguous = set()
    routine_used = priority_used = 0
    commitments = []
    for key, record in signals.items():
        if not isinstance(record, dict) or record.get('day') != day:
            continue
        parts = key.split('|')
        if len(parts) not in (3, 4) or parts[0] != 'EU-RESEARCH':
            continue
        symbol, old_phase = parts[1:3]
        rank = 2 if old_phase in ('INSTAPCHECK', 'BIJKOOPCHECK') else PHASE_RANK.get(old_phase, 0)
        if not rank:
            continue
        if record.get('delivery') != EXPIRED:
            previous_rank[symbol] = max(previous_rank.get(symbol, 0), rank)
        if record.get('delivery') in AMBIGUOUS:
            ambiguous.add(symbol)
        if (record.get('delivery') in AMBIGUOUS | {'sent'} and not record.get('capacity_released_utc')
                and isinstance(record.get('capacity'), dict)):
            commitments.append(record['capacity'])
        if uses_daily_budget(record):
            if record.get('priority_lane'):
                priority_used += 1
            else:
                routine_used += 1

    freshness, rows = assess_report(report, evidence, now=now, reviewer_pin=reviewer_pin,
                                    positions=positions, commitments=commitments)
    summary['report_status'] = freshness['reason']
    if not freshness['fresh']:
        return
    eligible = []
    for row in rows:
        symbol, stage = row['symbol'], row['recovery_phase']
        financial = row['financial_entry']
        score, owned = row.get('early_recovery_score'), symbol in holdings
        if 'shares' in financial or stage is not None:
            summary['financial_results'].append({'symbol': symbol, **financial})
        if stage is None:
            reasons['no_current_structure'] += 1
            continue
        capacity = financial.get('portfolio_capacity') or {}
        if capacity and capacity.get('status') != 'CAPACITY_VERIFIED':
            reasons['portfolio_' + capacity['status'].lower()] += 1
        if type(score) is not int or score < (2 if owned else 3):
            reasons['minimum_recovery_score'] += 1
            continue
        flags = row.get('historical_flags')
        if not isinstance(flags, list) or (not owned and 'BOTTOM-EVIDENCE-INSUFFICIENT' in flags):
            reasons['bottom_quality_gate'] += 1
            continue
        phase_counts[stage] += 1
        if symbol in ambiguous or PHASE_RANK[stage] <= previous_rank.get(symbol, 0):
            reasons['already_reserved_or_no_promotion'] += 1
            continue
        eligible.append((row, score, owned))
    def priority(item):
        row, score, owned = item
        return (-PHASE_RANK[row['recovery_phase']], -score,
                -int(row['symbol'] in priority_watch), -int(owned), row['symbol'])

    eligible.sort(key=priority)
    if eligible:
        store.require_exclusive_sender()
    attempts = 0
    while eligible:
        row, score, owned = eligible.pop(0)
        symbol, stage = row['symbol'], row['recovery_phase']
        send_time = clock()
        if (send_time.astimezone(ZoneInfo('Europe/Amsterdam')).date().isoformat() != day
                or not classify_eu_report(report, now=send_time)['fresh']):
            reasons['report_expired_before_send'] += 1
            break
        financial = {}
        if stage == FINANCIAL_ENTRY_CONFIRMED:
            financial = evaluate_entry(symbol, row.get('currency'), evidence.get(symbol),
                                       now=send_time, reviewer_pin=reviewer_pin, positions=positions,
                                       commitments=commitments)
        final_stage = recovery_phase(row, financial, now=send_time)
        if final_stage != stage:
            phase_counts[stage] -= 1
            reasons['evidence_expired_before_send'] += 1
            if final_stage is not None:
                phase_counts[final_stage] += 1
            for item in summary['financial_results']:
                if item['symbol'] == symbol:
                    item.update(financial_at_send=financial)
                    break
            if final_stage is not None:
                eligible.append(({**row, 'recovery_phase': final_stage}, score, owned))
                eligible.sort(key=priority)
            continue
        if stage is None or PHASE_RANK[stage] <= previous_rank.get(symbol, 0):
            continue
        priority_lane = (owned or symbol in priority_watch) and priority_used < 2
        if not priority_lane and routine_used >= 5:
            reasons['daily_cap'] += 1
            continue
        key = f'EU-RESEARCH|{symbol}|{stage}|{day}'
        if key in signals and signals[key].get('delivery') != EXPIRED:
            continue
        record = {'day': day, 'phase': stage, 'notification_schema_version': 16,
                  'priority_lane': priority_lane, 'notified_utc': send_time.isoformat()}
        if stage == FINANCIAL_ENTRY_CONFIRMED:
            record['capacity'] = financial['portfolio_capacity']
        body = f'{symbol} {stage} (herstelscore {score})\n' + broker_search_hint(symbol)
        if stage == EARLY_RECOVERY:
            body += 'Beginnend herstel in onderzoek. Volg de bodemstructuur en het verdere prijsverloop.'
        elif stage == DEGIRO_VERIFICATION:
            body += ('Controleer actuele DEGIRO bied/laat, eerste betekenisvolle weerstand, '
                     'structurele invalidatie, kosten, nieuws en portefeuilleruimte. '
                     'Providergegevens kunnen vertraagd zijn.')
        else:
            body += (f'Financieel bevestigd onderzoeksscenario voor {financial["shares"]} aandelen. '
                     f'Verwachte nettowinst EUR {financial["net_profit_eur"]:.2f} en '
                     f'netto R/R {financial["net_rr"]:.4f}. Controleer nieuws en portefeuilleruimte.')

        def still_current():
            checked = clock()
            if (checked.astimezone(ZoneInfo('Europe/Amsterdam')).date().isoformat() != day
                    or not classify_eu_report(report, now=checked)['fresh']):
                return False
            latest = financial
            if stage == FINANCIAL_ENTRY_CONFIRMED:
                latest = evaluate_entry(symbol, row.get('currency'), evidence.get(symbol),
                                        now=checked, reviewer_pin=reviewer_pin, positions=positions,
                                        commitments=commitments)
            return recovery_phase(row, latest, now=checked) == stage

        delivered = reserve_send(store, state, key, record, symbol,
                                 body + ' Handmatige beoordeling vereist. Geen koopopdracht.', sender,
                                 preflight=still_current)
        if delivered and 'capacity' in record:
            commitments.append(record['capacity'])
        if delivered:
            priority_used += int(priority_lane)
            routine_used += int(not priority_lane)
        else:
            reasons['evidence_expired_during_reservation'] += 1
        attempts += 1
        if attempts == 3:
            break
