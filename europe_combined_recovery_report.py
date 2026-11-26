"""Combine European historical, 15-minute and provider quote research."""
import json
from datetime import datetime, timezone
from pathlib import Path

from eu_entry_net import DISABLED, recovery_phase

ROOT = Path('reports')
NAME = 'europe_combined_recovery_report.json'


def combine(history, intraday, quotes, *, now):
    by_history = {row['symbol']: row for row in history['candidates']}
    by_quote = {row['symbol']: row for row in quotes['candidates']}
    rows = []
    for item in intraday['candidates']:
        symbol = item['symbol']
        historical = by_history[symbol]
        quote = by_quote.get(symbol, {})
        flags = historical.get('research_flags', [])
        score = item.get('early_recovery_score')
        if score is None:
            score = sum(item.get(key) is True for key in ('higher_last_low', 'above_prior_bar_high'))
        minimum = item.get('minimum_structure_score', 2)
        structure = score >= minimum
        data_ok = item.get('data_status') == 'INTRADAY-RESEARCH-ONLY'
        if not data_ok:
            structure_status = 'INTRADAY-DATA-BLOCKED'
        elif structure:
            structure_status = 'EARLY-STRUCTURE-OBSERVED'
        else:
            structure_status = 'NO-COMBINED-15M-CONFIRMATION'
        early_clue = any(item.get(key) is True for key in
                         ('higher_last_low', 'above_prior_bar_high', 'reclaim_recent_range'))
        early_watch = bool(data_ok and early_clue and 'STALE-DATA' not in flags
                           and historical.get('discovery_eligible', True))
        scenarios = historical.get('historical_3500_eur_scenarios') or {}
        money_pass = ((scenarios.get('rr_to_meaningful') or 0) >= 2
                      and (scenarios.get('meaningful_resistance_gross_eur') or 0) >= 150)
        further_only = (early_watch and not money_pass
                        and 'RR-BELOW-2-TO-1-AT-FIRST-MEANINGFUL; FURTHER-ZONE-REQUIRES-PASSAGE-VALIDATION' in flags
                        and (scenarios.get('rr_to_further') or 0) >= 2
                        and (scenarios.get('further_zone_gross_eur') or 0) >= 150)
        # Historical illustrations stay available for research. Only actual
        # broker inputs can establish or disprove present financial room.
        broker_candidate = bool(early_watch and structure)
        blocks = quote.get('execution_blocks', ['QUOTE-AUDIT-MISSING'])
        quote_fresh = quote.get('provider_freshness_pass') is True and 'CURRENCY-MISMATCH' not in blocks
        quote_delayed = (quote.get('provider_delayed_but_usable_for_attention') is True
                         and 'CURRENCY-MISMATCH' not in blocks)
        verify_now = broker_candidate and (quote_fresh or quote_delayed)
        fresh_handoff = broker_candidate and quote_fresh
        if fresh_handoff:
            status = 'DEGIRO-CHECK-NOW'
        elif verify_now:
            status = 'DEGIRO-VERIFY-NOW-DELAYED-PROVIDER'
        elif broker_candidate:
            status = 'BROKER-CHECK-CANDIDATE'
        elif early_watch:
            status = 'EARLY-RECOVERY-WATCH'
        else:
            status = 'WATCH/RESEARCH'
        row = {
            'symbol': symbol, 'sector': historical.get('sector'), 'currency': historical.get('currency'),
            'historical_close': historical.get('historical_close'),
            'drawdown_126d_pct': historical.get('drawdown_126d_pct'),
            'historical_status': historical.get('status'), 'historical_flags': flags,
            'historical_execution_blockers': historical.get('execution_blockers', []),
            'discovery_eligible': historical.get('discovery_eligible'),
            'historical_profit_reference_under_150_eur': historical.get('advisory_under_150_eur_reference', False),
            'historical_3500_eur_scenarios': historical.get('historical_3500_eur_scenarios'),
            'historical_first_friction': historical.get('first_friction'),
            'historical_meaningful_resistance': historical.get('first_meaningful_resistance'),
            'historical_further_zone': historical.get('further_recovery_zone'),
            'intraday_evidence': structure_status,
            'last_15m_bar': (item.get('latest_bar') or {}).get('time'),
            'higher_last_low': item.get('higher_last_low'), 'above_prior_bar_high': item.get('above_prior_bar_high'),
            'holding_recent_low': item.get('holding_recent_low'), 'reclaim_recent_range': item.get('reclaim_recent_range'),
            'early_recovery_score': score, 'session_phase': item.get('session_phase'), 'minimum_structure_score': minimum,
            'provider_1m_quote': quote.get('quote_close'), 'provider_1m_quote_utc': quote.get('quote_utc'),
            'provider_quote_age_seconds_at_run': quote.get('quote_age_seconds'),
            'provider_freshness_class': quote.get('provider_freshness_class'),
            'provider_freshness_pass': quote_fresh, 'provider_delayed_but_usable_for_attention': quote_delayed,
            'provider_bid': quote.get('provider_bid'), 'provider_ask': quote.get('provider_ask'),
            'provider_spread_pct': quote.get('provider_spread_pct'), 'execution_blocks': blocks,
            'early_recovery_watch': early_watch, 'broker_check_candidate': broker_candidate,
            'further_zone_research_only': further_only, 'broker_verify_now': verify_now,
            'degiro_check': fresh_handoff, 'degiro_check_now': fresh_handoff, 'prealert_status': status,
            'portfolio_fit_verified': False, 'broker_quote_verified': False, **DISABLED,
        }
        row['recovery_phase'] = recovery_phase(row, {}, now=now)
        rows.append(row)

    def symbols(key):
        return [row['symbol'] for row in rows if row.get(key)]

    data_blocked = [row['symbol'] for row in rows if row['intraday_evidence'] == 'INTRADAY-DATA-BLOCKED'
                    or row['provider_freshness_class'] in ('DATA-BLOCKED', 'NO-VALID-QUOTE')]
    missing_quote = [row['symbol'] for row in rows if row['intraday_evidence'] == 'EARLY-STRUCTURE-OBSERVED'
                     and row['provider_freshness_class'] in ('DATA-BLOCKED', 'NO-VALID-QUOTE', 'STALE-OR-TIMESTAMP-INVALID')]
    early, broker = symbols('early_recovery_watch'), symbols('broker_check_candidate')
    urgent, fresh = symbols('broker_verify_now'), symbols('degiro_check_now')
    return {
        'generated_utc': now.isoformat(), 'scope': 'European recovery research and provider evidence',
        'historical_universe': history.get('stored_symbols_examined'),
        'early_watchlist_eligible': intraday.get('watchlist_eligible_count'), 'joined_count': len(rows),
        'early_recovery_watch_count': len(early), 'early_recovery_watch_symbols': early,
        'broker_check_candidate_count': len(broker), 'broker_check_candidate_symbols': broker,
        'broker_verify_now_count': len(urgent), 'broker_verify_now_symbols': urgent,
        'degiro_check_count': len(fresh), 'degiro_check_symbols': fresh,
        'delayed_provider_verify_now_symbols': [symbol for symbol in urgent if symbol not in fresh],
        'data_blocked_count': len(data_blocked), 'data_blocked_symbols': data_blocked,
        'structure_present_but_fresh_quote_missing_count': len(missing_quote),
        'structure_present_but_fresh_quote_missing_symbols': missing_quote,
        'no_setup_claim_safe': not data_blocked, 'trade_ready_count': 0, **DISABLED, 'candidates': rows,
    }


def main():
    sources = [json.loads((ROOT / name).read_text()) for name in (
        'europe_swing_research.json', 'europe_intraday_confirmation.json', 'europe_quote_execution_audit.json')]
    report = combine(*sources, now=datetime.now(timezone.utc))
    (ROOT / NAME).write_text(json.dumps(report, indent=2, ensure_ascii=False))
    print(f"EU_RECOVERY_COMBINED: candidates={report['joined_count']}", flush=True)


if __name__ == '__main__':
    main()
