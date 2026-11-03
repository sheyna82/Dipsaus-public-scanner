# US intraday episode validation — existing infrastructure inventory

Audited 2026-11-03, research branch `research/offline-technical-risk-20261021`.

## Reuse; do not rebuild
- `us_momentum_recovery_discovery.py`: `chart(symbol,"1d","1m")` provides current-session 1-minute US bars via Yahoo chart. This is NOT a multi-month archive.
- `research/us_setup_existing_chart_adapter.py`: research-only adapter to existing `ts/low/close` rows; declared 1-minute interval is checked against timestamps.
- `research/us_setup_intraday_data_preflight.py`: rejects daily bars and invalid ordering.
- `research/us_setup_archive_coverage.py`: counts supplied archived sessions, but does not create an archive or verify independent labels.
- `research/swing_lifecycle/ohlcv_archive_audit.py` and `.github/workflows/research-ohlcv-archive-audit.yml`: existing read-only **daily** OHLCV JSONL archive audit; cannot validate minute bars without a separate schema.
- `research_prospective_archive.py`, `research_prospective_archive_restore.py`, `.github/workflows/prospective-archive-transport-research.yml`: existing synthetic prospective archive transport/restore; inspect and reuse before adding persistence.
- `research/us_independent_setup_replay.py`, `research/us_setup_episode_evaluation.py`, `research/us_setup_snapshot_contract.py`: detector, one-to-one matching, frozen snapshot.

## Confirmed GitHub artifacts, not yet inspected as intraday bars
- Run 41121367948: `candidate-feature-oos-historical-report` (GitHub reported 696922 bytes, not expired).
- Run 41121382015: `candidate-feature-oos` and several benchmark/integrated reports (not expired).
- Run 41531647491: `candidate-feature-oos` and other research reports (not expired).
- Artifact presence is NOT evidence of historical intraday bar coverage or independent episode labels. Inspect actual artifact contents and provenance before reuse.

## Blockers for genuine OOS claims
1. Obtain and inspect an actual multi-session, multi-month 1-minute OHLCV archive with exchange calendar, timezones, corporate actions and provider provenance. Current `1d/1m` call does not supply this.
2. Confirm existing archive/transport tools can persist such data across workflow runs; synthetic roundtrip alone does not prove cross-run retention.
3. Freeze chronological train/validation/test splits and blinded independently sourced episode labels. A label's `source` string alone does not establish independence.
4. Run baseline A/B and detector on the same held-out data; report raw sample sizes, false positives per ticker-day, recall, detection delay and uncertainty.
5. Keep notification eligibility false; no main merge, no live changes, no broker orders.

## Current status
Technical tests are not historical profitability evidence. No verified historical intraday archive, no independent labels, no measured out-of-sample episode performance.
