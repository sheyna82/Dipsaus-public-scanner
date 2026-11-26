"""Validate Yahoo chart data and keep metadata quotes separate from completed bars."""
import json
import math
import struct
import urllib.parse
import urllib.request
from datetime import datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

from us_schedule_gate import CLOSED_DAYS, EARLY_CLOSE_DAYS

CHART = 'https://query1.finance.yahoo.com/v8/finance/chart/'
NEW_YORK = ZoneInfo('America/New_York')
FIELDS = ('open', 'high', 'low', 'close', 'volume')
LISTING_START_UTC = {'SPCX': int(datetime(2026, 6, 12, tzinfo=timezone.utc).timestamp())}
MAX_MINUTE_AGE = 120
MINUTE_BAR_SOURCE = 'Yahoo Finance chart 1m'


def number(value):
    try:
        return type(value) in (int, float) and math.isfinite(value)
    except OverflowError:
        return False


def chart_payload(symbol, *, period, interval):
    query = urllib.parse.urlencode({'range': period, 'interval': interval, 'includePrePost': 'false'})
    url = CHART + urllib.parse.quote(symbol, safe='') + '?' + query
    request = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json'})
    with urllib.request.urlopen(request, timeout=15) as response:
        return json.load(response)


def chart_series(payload, symbol, interval):
    try:
        chart = payload['chart']
        results = chart['result']
        if chart.get('error') is not None or len(results) != 1:
            raise ValueError('INVALID_CHART_RESULT')
        result = results[0]
        meta, stamps = result['meta'], result['timestamp']
        quote = result['indicators']['quote'][0]
        columns = [quote[field] for field in FIELDS]
        if (not isinstance(stamps, list) or not stamps
                or any(not isinstance(column, list) or len(column) != len(stamps) for column in columns)):
            raise ValueError('OHLCV_LENGTH_MISMATCH')
        if (meta.get('symbol') != symbol or meta.get('currency') != 'USD'
                or meta.get('exchangeTimezoneName') != NEW_YORK.key
                or meta.get('dataGranularity') != interval):
            raise ValueError('CHART_SOURCE_IDENTITY_MISMATCH')
    except (AttributeError, KeyError, IndexError, TypeError) as exc:
        raise ValueError('INVALID_CHART_SCHEMA') from exc
    if any(type(stamp) is not int or not 0 < stamp <= 253402300799 for stamp in stamps):
        raise ValueError('INVALID_BAR_TIMESTAMP')
    if any(first >= second for first, second in zip(stamps, stamps[1:])):
        raise ValueError('DUPLICATE_OR_NONCHRONOLOGICAL_BARS')
    return meta, list(zip(stamps, *columns))


def checked_bar(stamp, opening, high, low, close, volume):
    prices = (opening, high, low, close)
    if all(price is None for price in prices) and (volume is None or type(volume) in (int, float) and volume == 0):
        return None
    if (not all(number(price) for price in prices) or not number(volume)
            or volume < 0 or not 0 < low <= min(opening, close) <= max(opening, close) <= high):
        raise ValueError('PARTIAL_OR_INCONSISTENT_OHLCV')
    return {'ts': stamp, 'open': opening, 'high': high, 'low': low, 'close': close, 'volume': volume}


def regular_session(meta):
    try:
        regular = meta['currentTradingPeriod']['regular']
        start, end = regular['start'], regular['end']
        if any(type(stamp) is not int or stamp % 60 for stamp in (start, end)):
            raise ValueError('INVALID_REGULAR_SESSION')
        start_local = datetime.fromtimestamp(start, NEW_YORK)
        end_local = datetime.fromtimestamp(end, NEW_YORK)
        if (start_local.date() != end_local.date() or start_local.weekday() >= 5
                or start_local.time() != time(9, 30) or not time(9, 30) < end_local.time() <= time(16)):
            raise ValueError('INVALID_REGULAR_SESSION')
    except (KeyError, TypeError, OverflowError, OSError) as exc:
        raise ValueError('INVALID_REGULAR_SESSION') from exc
    return start, end


def same_provider_price(a, b):
    if a == b:
        return True
    try:
        float32_a = struct.unpack('!f', struct.pack('!f', a))[0]
        float32_b = struct.unpack('!f', struct.pack('!f', b))[0]
    except OverflowError:
        return False
    return a == float32_b or b == float32_a


def minute_snapshot(payload, symbol, *, now):
    """Return the newest contiguous suffix of completed regular-session rows."""
    if now.utcoffset() is None:
        raise ValueError('NAIVE_MINUTE_CLOCK')
    meta, series = chart_series(payload, symbol, '1m')
    start, end = regular_session(meta)
    now_ts = now.timestamp()
    ref_stamp, ref_price = meta.get('regularMarketTime'), meta.get('regularMarketPrice')
    reference = None
    if (type(ref_stamp) is int and start <= ref_stamp <= end and ref_stamp <= now_ts
            and number(ref_price) and ref_price > 0):
        reference = {'ts': ref_stamp, 'price': ref_price}
    update_removed = False
    completed = []
    for index, values in enumerate(series):
        stamp = values[0]
        bar = checked_bar(*values)
        # An aligned flat bar within the session can be real. A row at the
        # session end has no regular-session minute to represent.
        if (index == len(series) - 1 and (stamp % 60 or stamp == end) and reference is not None
                and stamp == reference['ts'] and bar is not None and bar['volume'] == 0
                and bar['open'] == bar['high'] == bar['low'] == bar['close']
                and same_provider_price(bar['close'], reference['price'])):
            update_removed = True
            continue
        if stamp % 60 or not start <= stamp < end or stamp > now_ts:
            raise ValueError('BAR_OUTSIDE_REGULAR_MINUTE_GRID')
        if stamp + 60 <= now_ts:
            completed.append((stamp, bar))
    if not completed:
        raise ValueError('NO_COMPLETED_MINUTE_BAR')
    last_stamp, last = completed[-1]
    if last is None:
        raise ValueError('EMPTY_LAST_COMPLETED_MINUTE_BAR')
    contiguous = []
    expected = last_stamp
    for stamp, bar in reversed(completed):
        if stamp != expected or bar is None:
            break
        contiguous.append(bar)
        expected -= 60
    contiguous.reverse()
    age = now_ts - last_stamp
    expected_last = (int(min(now_ts, end)) // 60 - 1) * 60
    missing_latest = last_stamp != expected_last
    return {'symbol': symbol, 'source': MINUTE_BAR_SOURCE, 'source_verified': False,
            'reference': reference, 'latest_completed_bar': last, 'bars': contiguous,
            'completed_valid_count': sum(bar is not None for _, bar in completed),
            'empty_completed_count': sum(bar is None for _, bar in completed),
            'terminal_quote_update_removed': update_removed, 'bar_age_seconds': age,
            'latest_completed_minute_missing': missing_latest,
            'fresh': not missing_latest and 0 <= age <= MAX_MINUTE_AGE}


def fetch_minute_snapshot(symbol):
    payload = chart_payload(symbol, period='1d', interval='1m')
    return minute_snapshot(payload, symbol, now=datetime.now(timezone.utc))


def daily_bars(payload, symbol, *, now):
    """Return valid completed daily evidence for the fast and deep scans."""
    meta, series = chart_series(payload, symbol, '1d')
    session_start, session_end = regular_session(meta)
    now_ts = now.timestamp()
    if series[-1][0] > now_ts:
        raise ValueError('FUTURE_DAILY_BAR')
    session_date = datetime.fromtimestamp(session_start, NEW_YORK).date()
    rows = []
    for values in series:
        stamp = values[0]
        if stamp < LISTING_START_UTC.get(symbol, 0):
            continue
        stamp_date = datetime.fromtimestamp(stamp, NEW_YORK).date()
        if stamp_date == session_date and now_ts < session_end:
            continue
        bar = checked_bar(*values)
        if bar is not None and bar['volume'] > 0:
            bar['date'] = stamp_date.isoformat()
            rows.append(bar)
    return rows


def require_current_daily_history(rows, *, now):
    """Prevent a freshly fetched stale history from renewing discovery rights."""
    local = now.astimezone(NEW_YORK)
    expected = local.date()
    close = time(13) if expected in EARLY_CLOSE_DAYS else time(16)
    if local.time() < close:
        expected -= timedelta(days=1)
    while expected.weekday() >= 5 or expected in CLOSED_DAYS:
        expected -= timedelta(days=1)
    if rows and rows[-1]['date'] != expected.isoformat():
        raise ValueError('STALE_OR_FUTURE_DAILY_HISTORY')
