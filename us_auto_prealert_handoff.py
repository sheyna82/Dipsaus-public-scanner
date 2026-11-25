#!/usr/bin/env python3
"""Merge independent US discovery routes into a single per-ticker handoff."""
import json
import os
from datetime import datetime, timezone
from pathlib import Path

SRC = Path('reports/us_batch_runs')
MOM = Path('reports/us_momentum_recovery.json')
OUT = Path('reports/us_auto_prealert_candidates.json')
DISABLED = {'execution_ready': False, 'trade_ready': False, 'order_placement_enabled': False}


def deep_evidence(queued):
    dossier = queued.get('research_dossier') or {}
    triage = queued.get('research_triage') or {}
    zones = queued.get('pivot_zones') or []
    count = triage.get('bottom_signal_count')
    weekly = bool(triage.get('weekly_close_rising') or triage.get('weekly_higher_low'))
    identity = ((dossier.get('identity_crosscheck') or {}).get('status')
                or queued.get('identity_status') or 'IDENTITY_UNVERIFIED')
    eligible = bool(type(count) is int and count >= 3 and weekly and zones and identity != 'IDENTITY_MISMATCH')
    return {
        'name': queued.get('name'), 'auto_promoted': eligible,
        'discovery_lane': 'DEEP-RECOVERY', 'last_bar_date': queued.get('last_bar_date'),
        'historical_close_usd': dossier.get('historical_close_usd'), 'bottom_signal_count': count,
        'space_to_first_overhead_pct': triage.get('space_to_first_overhead_pct'),
        'weekly_structure_support': weekly, 'identity_status': identity,
        'profile_status': (dossier.get('issuer_profile') or {}).get('status') or queued.get('profile_status'),
        'historical_invalidation_reference_usd': dossier.get('historical_invalidation_reference_usd'),
        'historical_overhead_zones': zones[:3], 'company_event': dossier.get('company_event'),
        **DISABLED,
    }


def build_handoff(batch_reports, fast_report, *, now):
    rows = {}
    for report in batch_reports:
        for queued in report.get('deep_dive_queue', []):
            symbol = queued.get('symbol')
            if not isinstance(symbol, str) or not symbol:
                continue
            evidence = deep_evidence(queued)
            row = rows.setdefault(symbol, {'symbol': symbol, 'routes': {}})
            previous = row['routes'].get('deep')
            if previous is None or (evidence['auto_promoted'], evidence['last_bar_date'] or '') > (
                    previous['auto_promoted'], previous['last_bar_date'] or ''):
                row['routes']['deep'] = evidence
    for candidate in fast_report.get('candidates', []):
        symbol = candidate.get('symbol')
        if not isinstance(symbol, str) or not symbol:
            continue
        row = rows.setdefault(symbol, {'symbol': symbol, 'routes': {}})
        row['routes']['fast'] = {**candidate, **DISABLED, 'auto_promoted': True,
                                 'discovery_lane': 'FAST-MOMENTUM-RECOVERY'}
    for row in rows.values():
        fast, deep = row['routes'].get('fast'), row['routes'].get('deep')
        primary = fast or deep
        row.update(name=primary.get('name'), discovery_lane=primary['discovery_lane'],
                   auto_promoted=any(item['auto_promoted'] for item in row['routes'].values()), **DISABLED)
    selected = [rows[symbol] for symbol in sorted(rows)]
    return {'generated_utc': now.isoformat(), 'scope': 'Independent US recovery discovery routes',
            'prealert_symbols': [row['symbol'] for row in selected if row['auto_promoted']], 'rows': selected, **DISABLED}


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
