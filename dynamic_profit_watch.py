"""Private, persistent swing context; observed chart levels never become orders."""
from datetime import datetime, timedelta, timezone
from math import isfinite
from statistics import median


def number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and isfinite(value)


def timestamp(value):
    result = datetime.fromisoformat(value)
    if result.tzinfo is None:
        raise ValueError('BAR_TIMEZONE_REQUIRED')
    return result.astimezone(timezone.utc)


def bars(frame):
    result = []
    for index, row in frame.iterrows():
        values = {name.lower(): float(row[name]) for name in ('Open', 'High', 'Low', 'Close', 'Volume')}
        if not all(number(value) for value in values.values()):
            continue
        if not (0 < values['low'] <= min(values['open'], values['close']) <= max(values['open'], values['close']) <= values['high']):
            continue
        result.append(dict(values, time=index.to_pydatetime().isoformat()))
    return result


def completed(rows, now, duration):
    # Both left and right pivot evidence must use closed candles only.
    return sorted((r for r in rows if timestamp(r['time']) + duration <= now), key=lambda r: r['time'])


def pivots(rows, field, span=2):
    result = []
    for i in range(span, len(rows) - span):
        value = rows[i][field]
        neighbours = rows[i-span:i] + rows[i+1:i+span+1]
        valid = (value < min(r[field] for r in neighbours)) if field == 'low' else (value > max(r[field] for r in neighbours))
        if valid:
            result.append({'price': value, 'time': rows[i]['time'], 'confirmed_at': rows[i+span]['time'], 'index': i})
    return result


def structure(hourly, daily, quote, quote_time, now, previous=None):
    h = completed(hourly, now, timedelta(hours=1))
    d = completed(daily, now, timedelta(days=1))
    state = dict(previous or {})
    result = {'status': 'INSUFFICIENT-STRUCTURE-DATA', 'structure_alert': False, 'timeframe': '1h/1d', 'automatic_sell': False}
    if not number(quote) or quote <= 0:
        return result, state
    lows = pivots(h, 'low')
    reference = state.get('reference')
    # A new reference is a confirmed higher low with a subsequent rebound.
    # On first observation use the most recent recovery pair, not an obsolete leg.
    for prior, candidate in list(zip(lows, lows[1:]))[-1:]:
        rebound = max(r['close'] for r in h[candidate['index']+1:candidate['index']+3]) > h[candidate['index']]['high']
        if candidate['price'] > prior['price'] and rebound and (not reference or candidate['price'] > reference['price']) and (not reference or timestamp(candidate['time']) > timestamp(reference['time'])):
            reference = {k: candidate[k] for k in ('price', 'time', 'confirmed_at')}
    if reference:
        state['reference'] = reference
    result['reference'] = reference
    result['hourly_bar_count'] = len(h)
    result['daily_bar_count'] = len(d)
    if len(h) < 8 or len(d) < 5 or not reference:
        return result, state
    if timestamp(h[-1]['time']) < now - timedelta(hours=2):
        result['status'] = 'STALE-STRUCTURE-DATA'
        return result, state
    if timestamp(d[-1]['time']) < now - timedelta(days=5):
        result['status'] = 'STALE-DAILY-CONTEXT'
        return result, state
    ranges = [r['high'] - r['low'] for r in h[-21:-1]]
    tolerance = max(reference['price'] * .003, median(ranges) * .15)
    boundary = reference['price'] - tolerance
    lower_sequence = h[-1]['high'] < h[-2]['high'] and h[-1]['low'] < h[-2]['low']
    failure_to_reclaim = h[-1]['close'] < boundary and h[-2]['close'] < boundary and quote < boundary
    volume = h[-1]['volume'] > 1.5 * median(r['volume'] for r in h[-21:-1])
    daily_weak = d[-1]['close'] < d[-2]['close'] and d[-1]['low'] < d[-2]['low']
    fresh = -30 <= (now - timestamp(quote_time)).total_seconds() <= 120
    # Compare recent retests of this zone; proximity alone is never deterioration.
    same_zone_retests = sum(abs(r['low'] - reference['price']) <= tolerance and r['close'] >= reference['price'] for r in h[-20:])
    deteriorated = failure_to_reclaim and lower_sequence and (volume or daily_weak)
    result.update(status='STRUCTURE-REVIEW' if deteriorated else 'RECOVERY-STRUCTURE-WATCH',
                  structure_alert=bool(fresh and deteriorated), tolerance=tolerance,
                  same_zone_retests=same_zone_retests, failure_to_reclaim=failure_to_reclaim,
                  lower_high_lower_low=lower_sequence, volume_expansion=volume,
                  daily_context_weak=daily_weak, fresh_quote=fresh)
    return result, state


def chart_map(hourly, daily, quote, currency, item, now, fx=None):
    """Expose supported candidate zones plus exact missing inputs, never a verified target."""
    h = completed(hourly, now, timedelta(hours=1))
    d = completed(daily, now, timedelta(days=1))
    hour_highs = [p for p in pivots(h, 'high') if p['price'] > quote]
    day_highs = sorted((p for p in pivots(d, 'high') if p['price'] > quote), key=lambda p: p['price'])
    groups = []
    for p in day_highs:
        if groups and abs(p['price'] / median(x['price'] for x in groups[-1]) - 1) <= .0075:
            groups[-1].append(p)
        else:
            groups.append([p])
    repeated = [g for g in groups if len(g) >= 2]
    friction = min(hour_highs, key=lambda p: p['price'], default=None)
    meaningful = next((g for g in repeated if not friction or min(p['price'] for p in g) >= friction['price']), None)
    further = next((g for g in repeated if meaningful and min(p['price'] for p in g) > max(p['price'] for p in meaningful)), None)
    zone_records = {
        'first_friction': {'low': friction['price'], 'high': friction['price'], 'evidence_times': [friction['time']]} if friction else None,
        'first_meaningful_resistance': {'low': min(p['price'] for p in meaningful), 'high': max(p['price'] for p in meaningful), 'evidence_times': [p['time'] for p in meaningful]} if meaningful else None,
        'further_recovery_zone': {'low': min(p['price'] for p in further), 'high': max(p['price'] for p in further), 'evidence_times': [p['time'] for p in further]} if further else None,
    }
    missing = [name for name, zone in zone_records.items() if not zone]
    shares = item.get('shares')
    cost_eur = item.get('average_cost_eur')
    cost_usd = item.get('average_cost_usd')
    fx_ok = (currency == 'EUR' or (fx and number(fx.get('eurusd')) and fx['eurusd'] > 0 and -30 <= (now-timestamp(fx['time'])).total_seconds() <= 600))
    if not number(shares) or shares <= 0:
        missing.append('verified_position_size')
    if not (number(cost_eur) and cost_eur > 0) and not (currency == 'USD' and number(cost_usd) and cost_usd > 0):
        missing.append('verified_average_cost')
    if not fx_ok:
        missing.append('fresh_usd_eur_conversion')
    profits = {}
    if not any(x in missing for x in ('verified_position_size', 'verified_average_cost', 'fresh_usd_eur_conversion')):
        rate = 1 if currency == 'EUR' else fx['eurusd']
        for name, z in zone_records.items():
            if z:
                profits[name] = round(shares * ((z['low'] / rate - cost_eur) if number(cost_eur) and cost_eur > 0 else (z['low'] - cost_usd) / rate), 2)
    return {'status': 'CHART-CANDIDATES-ONLY', 'currency': currency, 'zones': zone_records,
            'gross_profit_eur_at_zones': profits, 'missing': missing,
            'profit_basis': 'provider_price_gain_converted_at_current_fx' if currency=='USD' and not number(cost_eur) else 'provider_eur_value_minus_verified_eur_cost',
            'broker_listing_currency_reconciliation_required': currency != item.get('broker_currency',currency),
            'broker_execution_verified': False, 'event_risk_verified': False,
            'further_zone_is_not_a_price_prediction': True, 'automatic_sell': False}


def evaluate(ticker, item, quote, quote_time, currency, now, previous=None, fx=None):
    state = dict(previous or {})
    identity = {'provider_symbol': item.get('provider_symbol'), 'currency': currency, 'swing_id': item.get('swing_id')}
    if state.get('identity') != identity:
        state = {'identity': identity}
    cache = state.get('cache') or {}
    if not cache or now.replace(minute=0,second=0,microsecond=0) != timestamp(cache['fetched_utc']).replace(minute=0,second=0,microsecond=0):
        try:
            hourly_frame = ticker.history(period='1mo', interval='1h', prepost=False, auto_adjust=False)
            daily_frame = ticker.history(period='6mo', interval='1d', prepost=False, auto_adjust=False)
            if hourly_frame.empty or daily_frame.empty:
                raise ValueError('HISTORY_EMPTY')
            split_rows = daily_frame[daily_frame.get('Stock Splits', 0) != 0] if 'Stock Splits' in daily_frame else []
            if len(split_rows):
                latest_split = split_rows.index[-1].to_pydatetime().isoformat()
                if item.get('corporate_action_verified_at') != latest_split:
                    return {'status': 'CORPORATE-ACTION-REVIEW-REQUIRED', 'structure_alert': False}, state, {'status': 'BLOCKED-CORPORATE-ACTION'}
            cache = {'fetched_utc': now.isoformat(), 'hourly': bars(hourly_frame), 'daily': bars(daily_frame)}
            state['cache'] = cache
        except Exception:
            # Preserve the ratcheted reference, but never claim fresh structure after a provider error.
            return {'status': 'STRUCTURE-DATA-BLOCKED', 'structure_alert': False}, state, {'status': 'STRUCTURE-DATA-BLOCKED'}
    observed, next_state = structure(cache['hourly'], cache['daily'], quote, quote_time, now, state)
    mapping = chart_map(cache['hourly'], cache['daily'], quote, currency, item, now, fx)
    return observed, next_state, mapping
