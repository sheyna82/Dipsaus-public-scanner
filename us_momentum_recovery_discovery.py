#!/usr/bin/env python3
"""Broad, fast US recovery discovery.

Discovery is intentionally broader than execution. It searches liquid large/mid-cap
US stocks from both most-active and day-gainer universes, then recognises an
intraday bottom -> higher-low -> reclaim pattern. Research/pre-alert only; never a
buy signal.
"""
import csv, json, os, re, urllib.parse, urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from us_intraday_recovery import intraday_structure
from us_yahoo_bars import chart_payload, daily_bars, fetch_minute_snapshot, number, require_current_daily_history

OUT=Path("reports/us_momentum_recovery.json")
HEADERS={"User-Agent":"Mozilla/5.0 (compatible; DipsausMomentum/2.0)"}
SCREENER="https://query1.finance.yahoo.com/v1/finance/screener/predefined/saved"

def get_json(url, params=None):
    if params: url += "?" + urllib.parse.urlencode(params)
    req=urllib.request.Request(url,headers=HEADERS)
    with urllib.request.urlopen(req,timeout=15) as r: return json.loads(r.read().decode())

def universe():
    """Broad official US equity universe; Yahoo screeners only enrich current quote metadata."""
    found={}
    urls=(
      "https://www.nasdaqtrader.com/dynamic/SymDir/nasdaqlisted.txt",
      "https://www.nasdaqtrader.com/dynamic/SymDir/otherlisted.txt",
    )
    for url in urls:
        req=urllib.request.Request(url,headers=HEADERS)
        with urllib.request.urlopen(req,timeout=20) as r:
            raw=r.read().decode("utf-8-sig")
        rows=csv.DictReader((line for line in raw.splitlines() if not line.startswith("File Creation Time")),delimiter="|")
        for row in rows:
            symbol=(row.get("Symbol") or row.get("NASDAQ Symbol") or row.get("ACT Symbol") or "").strip()
            name=(row.get("Security Name") or "").strip()
            if row.get("Test Issue")!="N" or row.get("ETF")!="N": continue
            if not re.fullmatch(r"[A-Z]{1,5}",symbol): continue
            low=name.lower()
            if any(x in low for x in ("warrant"," right"," unit","preferred","preference"," etf"," fund"," note"," bond")): continue
            found[symbol]={"symbol":symbol,"shortName":name}
    # Enrich symbols already present in official lists; never let Yahoo ranking define discovery coverage.
    for screen in ("most_actives","day_gainers","day_losers"):
        try:
            d=get_json(SCREENER,{"formatted":"false","lang":"en-US","region":"US","scrIds":screen,"count":100,"corsDomain":"finance.yahoo.com"})
            for q in d.get("finance",{}).get("result",[{}])[0].get("quotes",[]):
                symbol=q.get("symbol")
                if symbol in found and q.get("quoteType") in (None,"EQUITY"):
                    found[symbol].update(q, fast_ranked=True)
        except Exception:
            pass
    return list(found.values())

def discovery_gate(drawdown, rebound, turnover, change, structural):
    """Discovery only: retain liquid sold-off names before a completed turn."""
    sold_off_watch=bool(drawdown<=-15 and 0<=rebound<=20 and turnover>=50_000_000)
    momentum_watch=bool(structural or (number(change) and change>=1.0))
    return momentum_watch or sold_off_watch, sold_off_watch

def scan_candidate(issuer):
    symbol = issuer['symbol']
    cap = issuer.get('marketCap')
    if number(cap) and cap < 2_000_000_000:
        return 'below_known_market_cap', None
    payload = chart_payload(symbol, period='3mo', interval='1d')
    checked = datetime.now(timezone.utc)
    daily = daily_bars(payload, symbol, now=checked)
    require_current_daily_history(daily, now=checked)
    if len(daily) < 35:
        return 'insufficient_daily_history', None
    peak = max(bar['high'] for bar in daily[-60:])
    trough = min(bar['low'] for bar in daily[-20:])
    prior_close = daily[-1]['close']
    turnover = sum(bar['close'] * bar['volume'] for bar in daily[-20:]) / 20
    drawdown = (trough / peak - 1) * 100
    if prior_close < 1 or drawdown > -8 or turnover < 50_000_000:
        return 'outside_recovery_or_liquidity_gate', None

    snapshot, minute_status = None, 'VALID'
    try:
        snapshot = fetch_minute_snapshot(symbol)
    except ValueError as exc:
        minute_status = str(exc)
    except OSError:
        minute_status = 'MINUTE_PROVIDER_UNAVAILABLE'
    fresh = snapshot is not None and snapshot['fresh']
    price = snapshot['latest_completed_bar']['close'] if fresh else prior_close
    if snapshot is not None and not fresh:
        minute_status = 'STALE_COMPLETED_BAR'
    structure = intraday_structure(snapshot['bars']) if fresh else {}
    structural = structure.get('quality') is True
    early = structure.get('early_recovery_observed') is True
    change = (price / prior_close - 1) * 100 if fresh else None
    rebound = (price / trough - 1) * 100
    promising, sold_off = discovery_gate(drawdown, rebound, turnover, change, structural or early)
    if rebound > 35 or (rebound < 0 and not early) or not promising:
        return ('discovery_gate_rejected' if fresh else 'minute_data_unavailable'), None
    return 'qualified', {
        'symbol': symbol, 'name': issuer.get('shortName') or issuer.get('longName'),
        'last_bar_date': daily[-1]['date'], 'observed_utc': datetime.now(timezone.utc).isoformat(),
        'status': ('STRUCTURE-RECOGNISED' if structural else 'EARLY-RECOVERY-RESEARCH' if early
                   else 'SOLD-OFF-RECOVERY-WATCH' if sold_off else 'DISCOVERY-WATCH'),
        'sold_off_recovery_watch': sold_off, 'structure_quality_pass': structural,
        'early_recovery_observed': early, 'minute_data_status': minute_status,
        'reference_price_usd': (snapshot.get('reference') or {}).get('price') if snapshot else None,
        'reference_quote_ts': (snapshot.get('reference') or {}).get('ts') if snapshot else None,
        'completed_minute_bar': snapshot['latest_completed_bar'] if snapshot else None,
        'completed_minute_bar_age_seconds': snapshot['bar_age_seconds'] if snapshot else None,
        'source_verified': False, 'day_change_pct': change,
        'recent_peak_usd': peak, 'recent_20d_trough_usd': trough,
        'recent_drawdown_pct': drawdown, 'rebound_from_20d_trough_pct': rebound,
        'avg_20d_dollar_turnover_usd': round(turnover), 'market_cap_usd': cap if number(cap) else None,
        'intraday_structure': structure, 'execution_ready': False, 'trade_ready': False,
        'order_placement_enabled': False,
    }


def main():
    from collections import Counter

    issuers = universe()
    if not issuers:
        raise RuntimeError('US_FAST_UNIVERSE_EMPTY')
    sweep = int(os.environ.get('US_FAST_SWEEP', '0'))
    # Bounded fast pass. Deeper batches carry broad coverage without making
    # early discovery wait for the entire US universe or a market cap lookup.
    ranked = [issuer for issuer in issuers if issuer.get('fast_ranked')]
    ranked.sort(key=lambda item: (-(item.get('regularMarketVolume') if number(item.get('regularMarketVolume')) else 0),
                                  item['symbol']))
    monitor = sorted((issuer for issuer in issuers if not issuer.get('fast_ranked')),
                     key=lambda item: item['symbol'])
    if monitor:
        start = (sweep * 72) % len(monitor)
        monitor = (monitor[start:] + monitor[:start])[:72]
    sample = ranked[:72] + monitor
    candidates, failures, audit = [], {}, Counter()
    outcomes = dict.fromkeys((issuer['symbol'] for issuer in sample), 'timeout_unfinished')
    pool = ThreadPoolExecutor(max_workers=8)
    futures = {pool.submit(scan_candidate, issuer): issuer['symbol'] for issuer in sample}
    try:
        for future in as_completed(futures, timeout=290):
            try:
                outcome, candidate = future.result()
                audit[outcome] += 1
                outcomes[futures[future]] = outcome
                if candidate is not None:
                    candidates.append(candidate)
            except (OSError, ValueError) as exc:
                failures[futures[future]] = type(exc).__name__
                outcomes[futures[future]] = 'provider_error'
    except TimeoutError:
        audit['timeout_unfinished'] = len(sample) - sum(audit.values()) - len(failures)
    finally:
        pool.shutdown(wait=False, cancel_futures=True)
    if not any(audit[key] for key in ('qualified', 'discovery_gate_rejected', 'outside_recovery_or_liquidity_gate', 'below_known_market_cap', 'minute_data_unavailable')):
        raise RuntimeError('US_FAST_NO_USABLE_DAILY_EVIDENCE')
    candidates.sort(key=lambda item: (not item['early_recovery_observed'], not item['structure_quality_pass'],
                                     -(item['day_change_pct'] or 0), item['symbol']))
    for rank, candidate in enumerate(candidates, start=1):
        candidate['discovery_rank'] = rank
    output = Path(os.environ.get('US_FAST_REPORT', OUT))
    output.parent.mkdir(parents=True, exist_ok=True)
    report = {'generated_utc': datetime.now(timezone.utc).isoformat(),
              'scope': 'Bounded fast recovery discovery using ranked and rotating official US equities',
              'coverage_audit': {**audit, 'universe_total': len(issuers), 'requested': len(sample)},
              'candidate_count': len(candidates), 'candidates': candidates, 'outcomes': outcomes, 'failures': failures,
              'trade_ready': False, 'order_placement_enabled': False}
    output.write_text(json.dumps(report, indent=2))
    print(f'US_FAST_RECOVERY: candidates={len(candidates)}')


if __name__ == '__main__':
    main()
