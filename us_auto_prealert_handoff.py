#!/usr/bin/env python3
"""Translate fast and deep reports to explicit, independent research observations."""
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from eu_entry_net import age_seconds
from us_recovery_continuity import DEFERRED, QUALIFIED, REJECTED, REVOKED, UNAVAILABLE

SRC = Path('reports/us_batch_runs')
MOM = Path('reports/us_momentum_recovery.json')
OUT = Path('reports/us_auto_prealert_candidates.json')
DISABLED = {'execution_ready': False, 'trade_ready': False, 'order_placement_enabled': False}


def deep_evidence(item, batch):
    dossier = item.get('research_dossier') or {}
    triage = item.get('research_triage') or {}
    recovery = item.get('recovery_map') or {}
    zones = item.get('pivot_zones') or recovery.get('historical_overhead_pivot_zones') or []
    count = triage.get('bottom_signal_count')
    weekly = bool(triage.get('weekly_close_rising') or triage.get('weekly_higher_low'))
    identity = ((dossier.get('identity_crosscheck') or {}).get('status')
                or item.get('identity_status') or 'IDENTITY_UNVERIFIED')
    eligible = bool(type(count) is int and count >= 3 and weekly and zones and identity != 'IDENTITY_MISMATCH')
    return {
        'name': item.get('name'), 'auto_promoted': eligible, 'source_batch': batch,
        'discovery_lane': 'DEEP-RECOVERY', 'last_bar_date': item.get('last_bar_date'),
        'historical_close_usd': dossier.get('historical_close_usd', item.get('last_close_usd')),
        'bottom_signal_count': count, 'space_to_first_overhead_pct': triage.get('space_to_first_overhead_pct'),
        'weekly_structure_support': weekly, 'identity_status': identity,
        'profile_status': (dossier.get('issuer_profile') or {}).get('status') or item.get('profile_status'),
        'historical_invalidation_reference_usd': dossier.get('historical_invalidation_reference_usd',
                                                                recovery.get('recent_10d_low_invalidation_reference_usd')),
        'historical_overhead_zones': zones[:3], 'company_event': dossier.get('company_event'),
        'early_turn': triage.get('early_turn'), **DISABLED,
    }


def build_handoff(batch_reports, fast_report, *, now):
    events = {}

    def record(symbol, lane, status, observed, evidence=None):
        if not isinstance(symbol, str) or not symbol:
            return
        age = age_seconds(observed, now)
        if age is None or age < 0:
            return
        lanes = events.setdefault(symbol, {})
        lanes.setdefault(lane, []).append({'status': status, 'observed_utc': observed, 'evidence': evidence})

    for report in batch_reports:
        observed = report.get('finished_utc') or report.get('run_utc')
        batch = report.get('batch_index')
        screened = set(report.get('completed_symbols', []))
        failed = set(report.get('failures', {}))
        shortlist = {row['symbol']: row for row in report.get('identity_shortlist', [])}
        candidates = {row['symbol']: row for row in report.get('candidates', [])}
        queued = {row['symbol']: row for row in report.get('deep_dive_queue', [])}
        exclusions = report.get('queue_exclusions', {})
        rejected = set(exclusions.get('near_overhead', [])) | set(exclusions.get('liquidity_review', []))
        symbols = set(report.get('sample_symbols', [])) | candidates.keys() | queued.keys()
        for symbol in sorted(symbols):
            identity = shortlist.get(symbol, {})
            item = queued.get(symbol) or candidates.get(symbol)
            evidence = deep_evidence({**item, **identity}, batch) if item else None
            if symbol in failed:
                status = UNAVAILABLE
            elif identity.get('identity_status') == 'IDENTITY_MISMATCH' or (evidence and evidence['identity_status'] == 'IDENTITY_MISMATCH'):
                status = REVOKED
            elif symbol in queued and evidence['auto_promoted']:
                status = QUALIFIED
            elif symbol in rejected:
                status = REJECTED
            elif evidence:
                status = DEFERRED
            else:
                status = REJECTED if symbol in screened else UNAVAILABLE
            record(symbol, 'deep', status, observed, evidence)

    observed = fast_report.get('generated_utc')
    fast_candidates = {row['symbol']: row for row in fast_report.get('candidates', [])}
    outcomes = fast_report.get('outcomes', {})
    for symbol in sorted(outcomes.keys() | fast_candidates.keys() | fast_report.get('failures', {}).keys()):
        item = fast_candidates.get(symbol)
        raw = outcomes.get(symbol)
        evidence = None
        if item:
            evidence = {**item, **DISABLED, 'auto_promoted': True, 'discovery_lane': 'FAST-MOMENTUM-RECOVERY'}
            status = QUALIFIED if item.get('minute_data_status', 'VALID') == 'VALID' else UNAVAILABLE
        elif raw in ('below_known_market_cap', 'outside_recovery_or_liquidity_gate', 'discovery_gate_rejected'):
            status = REJECTED
        else:
            status = UNAVAILABLE
        record(symbol, 'fast', status, (item or {}).get('observed_utc') or observed, evidence)

    rows = []
    for symbol, lanes in events.items():
        latest = {lane: min(items, key=lambda event: age_seconds(event['observed_utc'], now)) for lane, items in lanes.items()}
        routes = {lane: event['evidence'] for lane, event in latest.items() if event['evidence']}
        if routes:
            primary = routes.get('fast') or routes['deep']
            rows.append({'symbol': symbol, 'name': primary.get('name'),
                         'discovery_lane': primary['discovery_lane'], 'routes': routes,
                         'auto_promoted': any(event['status'] == QUALIFIED for event in latest.values()), **DISABLED})
    rows.sort(key=lambda row: row['symbol'])
    return {'generated_utc': now.isoformat(), 'scope': 'Independent US recovery discovery routes',
            'prealert_symbols': [row['symbol'] for row in rows if row['auto_promoted']],
            'lane_events': events, 'rows': rows, **DISABLED}


def read_report(path):
    try:
        report = json.loads(path.read_text())
        return report if isinstance(report, dict) else {}
    except (OSError, ValueError):
        return {}


def main():
    batch_dir = Path(os.environ.get('US_BATCH_REPORT_DIR', SRC))
    fast_path = Path(os.environ.get('US_FAST_REPORT', MOM))
    report = build_handoff([read_report(path) for path in sorted(batch_dir.glob('batch_*.json'))],
                           read_report(fast_path), now=datetime.now(timezone.utc))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2))
    print(f"US_HANDOFF: tickers={len(report['rows'])}")


if __name__ == '__main__':
    main()
