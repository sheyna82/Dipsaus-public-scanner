# DIPSAUS — historical OOS replay recovery route (2026-11-05)

## New verified source paths

Historical branch `research/offline-technical-risk-20261021` contains:
- `.github/workflows/candidate-feature-oos-report.yml`: an existing **manual workflow_dispatch** that runs historical candidate OOS evaluation, saves a frozen input snapshot, replays the report from the snapshot, compares candidate/portfolio results and SHA-derived input provenance, and publishes three report artifacts.
- `research/candidate_feature_oos.py`: uses a training-only 65% per-symbol threshold fit and a subsequent held-out candidate cohort; the method and candidate universe still require independent audit.
- `research/candidate_input_reproducibility.py`: compares per-symbol and benchmark hashes across reports, but explicitly cannot prove code identity or raw data correctness.
- `research/candidate_entry_snapshot.py`: a provider acquisition module with potential source drift; a new fetch is **not** identical to the original historical raw bars.

## Recover without contaminating evidence

1. Identify a specific successful `candidate-feature-oos-report.yml` workflow run and retrieve its published `candidate_feature_oos_input_snapshot.json`, `candidate_feature_oos.json`, and `candidate_feature_portfolio_quarters.json` if still available.
2. Verify workflow run ID, head commit, artifact ID, SHA256 for each downloaded byte stream, source timestamps and adjustment policies. If any snapshot is missing, mark the run `UNRECOVERABLE_FROZEN_INPUT` rather than substituting fresh provider data.
3. Run the older branch's **existing** snapshot replay using that frozen artifact. Compare report content and provenance hashes. Historical OOS does not automatically equal prospective validation.
4. Inspect candidate-level fields for chronological entry/exit and return values, instrument IDs, and signal priority. Preserve original selection as-of evidence. Only then adapt the ledger to the new capital sizing scenarios.
5. If original snapshots cannot be recovered, register a **new** experiment before fetching any data, and keep it distinct from the prior 96-entry experiment.

## Explicit limitations

The run listing for historical workflow `40316862372` returned no available artifacts; this does **not** establish the artifact status of all other workflows. The currently discovered OOS workflow path establishes an executable **recovery route**, not that its historical frozen snapshot has been recovered. No independent raw data validation or new backtest was performed in this checkpoint.

**Decision:** `SEARCH_FROZEN_OOS_ARTIFACT_FIRST`. Research-only; no live changes, broker data publication or trading recommendation.
