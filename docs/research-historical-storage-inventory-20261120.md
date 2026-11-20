# Historical signal storage inventory — research only (2026-11-20)

Scope: read-only inspection of public branch `research/net-execution-math-20261119`.
No private state files, tokens, holdings, report contents or private identifiers were fetched.

## Confirmed architecture from source code

- `.github/workflows/shadow-us.yml` and `shadow-eu.yml` call `safe_runner.py`
  with private runtime secrets. They deliberately disable public report artifacts,
  report summaries, caches and report commits.
- `private_runtime.PrivateStore` obtains its destination from the
  `SCANNER_STATE_REPOSITORY` environment variable, validates that it is private,
  and reads/writes state through GitHub Contents API. This public source does not
  disclose the actual configured destination.
- `safe_runner.py` persists **latest** report/state snapshots, including
  `latest_watch_reports`, `latest_unified_research`,
  `latest_eur_upside_research`, `latest_eu_report` and
  `latest_us_reports`. A bounded `eu_freshness_history` exists, but is not
  a documented historical candidate/outcome ledger.
- `latest_us_reports` uses the current `reports/us_batch_runs/*.json` set.
  A key called `latest_*` does not prove retention of prior runs.
- `research_walk_forward_validation.py` and
  `research_historical_coverage.py` consume caller-supplied historical records.
  They do **not** fetch or authenticate scanner history.

## Backtest readiness

**BLOCKED — historical candidate universe and forward outcomes not established.**
There is no evidence from the inspected public files of a complete, immutable,
point-in-time archive containing every selected, rejected and deferred candidate,
its contemporaneous input features, and an independently observed later outcome.

Do not use current/latest snapshots as historical features: that risks
look-ahead and survivorship bias. Do not expose private state to public GitHub
Actions logs, artifacts or commits.

## Next verification (private, authorized channel only)

1. Inspect only storage **schema, key names, retention policy and record counts**;
   never print tickers, holdings, quotes, secrets or raw reports.
2. Determine whether an append-only historical ledger already exists and whether
   it includes rejected/deferred signals and outcomes. Treat missing history as
   unavailable, not as zero-return observations.
3. Define a privacy-preserving export contract and independent outcome provenance
   before implementing any historical backfill or performance claims.
4. Require explicit review before any changes to private state, production
   scanner execution or notification flows.

Research ranking remains heuristic; `trade_ready=False` and
`order_placement_enabled=False`.
