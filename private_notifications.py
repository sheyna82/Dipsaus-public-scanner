"""Selective phase upgrades and profit decisions. Reserve before sending; no duplicate retries."""
import json
import os
from pathlib import Path
from datetime import datetime, timezone
import urllib.request

RANK = {'BOTTOM-RECOVERY': 1, 'BREAKOUT-SEEN': 2, 'BREAKOUT-HOLD-RETEST': 3, 'EXECUTION-NEAR': 4}


def phase(row):
    text = ' '.join(str(row.get(k, '')) for k in ('status', 'triggered_route', 'trigger_route', 'route', 'setup_phase')).upper()
    yes = lambda *keys: any(bool(row.get(k)) for k in keys)
    breakout = yes('breakout_observed', 'breakout_seen', 'breakout_confirmed') or 'BREAKOUT' in text
    hold = yes('breakout_hold_observed', 'retest_hold_observed', 'hold_observed', 'higher_low_observed', 'recent_reclaim_observed')
    if row.get('market') == 'US':
        hold = hold or yes('reclaim_observed') or ('RETEST' in text and ('HOLD' in text or 'TURN' in text))
    execution = yes('execution_near', 'buy_ready', 'execution_qualified') or any(x in text for x in ('BUY-READY', 'KOOPKLAAR', 'EXECUTION-NEAR', 'VERY-NEAR-BUY-READY'))
    if execution: return 'EXECUTION-NEAR'
    if breakout and hold: return 'BREAKOUT-HOLD-RETEST'
    if breakout: return 'BREAKOUT-SEEN'
    return 'BOTTOM-RECOVERY'


def reserve_send(store, state, key, record, symbol, body, sender=None):
    # An uncertain network delivery remains reserved, preventing duplicate pushes.
    record['delivery'] = 'reserved'
    state['signals'][key] = record
    store.save(state)
    if sender:
        sender(symbol, body)
    else:
        topic = os.environ.get('NTFY_TOPIC', '')
        if not topic: raise RuntimeError('NOTIFICATION_SECRET_NOT_CONFIGURED')
        import re
        if not re.fullmatch(r'[A-Za-z0-9_-]+', topic):
            raise RuntimeError('NOTIFICATION_TOPIC_INVALID')
        req = urllib.request.Request('https://ntfy.sh/' + topic, data=body.encode(), method='POST',
            headers={'Title': 'DIPSAUS - ' + symbol, 'Priority': '5'})
        try:
            with urllib.request.urlopen(req, timeout=15): pass
        except Exception:
            raise RuntimeError('NOTIFICATION_DELIVERY_UNCERTAIN') from None
    record['delivery'] = 'sent'
    store.save(state)


def notify(store, state, entries, exits, sender=None):
    store.require_exclusive_sender()
    for row in entries:
        if not row.get('prealert_trigger_observed'): continue
        market = row.get('market', 'EU')
        if market == 'US' and not row.get('watch_type'): continue
        route = row.get('triggered_route') or row.get('trigger_route') or 'PRE-ALERT'
        if row.get('watch_type') == 'PORTFOLIO-REENTRY' and route not in (
            'ACTIVE-HOLDING-DIP-TURN', 'ACTIVE-HOLDING-BASE-TEST', 'ACTIVE-HOLDING-MULTIDAY-RECOVERY'):
            continue
        symbol = row.get('symbol', 'UNKNOWN'); ph = phase(row)
        key = f'ENTRY|{market}|{symbol}|PHASE'
        prev = state['signals'].get(key, {})
        if RANK[ph] <= RANK.get(prev.get('phase'), 0): continue
        record = {'phase': ph, 'notification_schema_version': 9,
                  'notified_utc': datetime.now(timezone.utc).isoformat()}
        if ph == 'BOTTOM-RECOVERY':
            state['signals'][key] = record; store.save(state); continue
        body = f'{symbol}: {ph}\nProvider quote: {row.get("provider_quote")}\nDEGIRO check: bid/ask/spread, current-leg invalidation, R/R>=2, dynamic sizing, realistic EUR recovery profit, news/events and portfolio fit. No chase; no automatic order.'
        reserve_send(store, state, key, record, symbol, body, sender)
    for row in exits:
        symbol = row.get('symbol', 'UNKNOWN'); key = f'EXIT|{symbol}|STATE'
        prev = state['signals'].get(key, {})
        if not row.get('profit_alert'):
            if prev.get('active'):
                state['signals'][key] = {'active': False}; store.save(state)
            continue
        reason = row.get('alert_reason') or 'DECISION-ZONE'; decision = row.get('decision') or 'WINSTCHECK'
        sid = f'{reason}|{decision}'
        if prev.get('active') and prev.get('state_id') == sid: continue
        record = {'active': True, 'state_id': sid, 'notification_schema_version': 9,
                  'notified_utc': datetime.now(timezone.utc).isoformat()}
        body = f'{symbol}: WINSTCHECK NU\nReason: {reason}\nProvider quote: {row.get("provider_quote")}\nNo automatic sale. Verify current DEGIRO bid/ask, recovery structure and momentum.'
        reserve_send(store, state, key, record, symbol, body, sender)

def notify_eu_research(store, state, report, holdings, sender=None):
    """One broker-verification prompt per new EU setup; never a buy instruction."""
    from datetime import timedelta
    now = datetime.now(timezone.utc)
    try:
        generated = datetime.fromisoformat(report["generated_utc"].replace("Z", "+00:00"))
    except (KeyError, ValueError, TypeError):
        return
    if generated.tzinfo is None or not timedelta(0) <= now - generated <= timedelta(minutes=25):
        return
    for row in report.get("candidates", []):
        if not row.get("broker_verify_now") or row.get("trade_ready") or not row.get("broker_check_candidate"):
            continue
        symbol = row.get("symbol")
        if not isinstance(symbol, str) or not symbol or not row.get("provider_delayed_but_usable_for_attention") and not row.get("provider_freshness_pass"):
            continue
        # Historical calculations are research inputs, not verified executable R/R.
        scenarios = row.get("historical_3500_eur_scenarios") or {}
        if (scenarios.get("rr_to_meaningful") or 0) < 2 or (scenarios.get("meaningful_resistance_gross_eur") or 0) < 150:
            continue
        kind = "BIJKOOPCHECK" if symbol in holdings else "INSTAPCHECK"
        key = f"EU-RESEARCH|{symbol}|{kind}"
        previous = state.setdefault("signals", {}).get(key, {})
        # Alert at most once per symbol per trading day, not on every five-minute check.
        if previous.get("day") == generated.date().isoformat():
            continue
        record = {"day": generated.date().isoformat(), "notification_schema_version": 10,
                  "notified_utc": now.isoformat()}
        body = (f"{symbol}: {kind} - vroege herstelkandidaat, GEEN koopbevestiging.\\n"
                "Providerdata kan vertraagd zijn. Controleer actuele DEGIRO bied/laat, "
                "zelfstandige herstelstructuur, eerste betekenisvolle weerstand, R/R >=2, "
                "brutowinst >= EUR150 bij standaardtranche, nieuws/earnings en portefeuillerisico. "
                "Geen automatische order.")
        reserve_send(store, state, key, record, symbol, body, sender)
