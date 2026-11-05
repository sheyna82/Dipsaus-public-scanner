# DIPSAUS — Historical OOS artifact recovery checkpoint (2026-11-05)

## Verified via GitHub API

- Historical workflow run: https://github.com/sheyna82/Dipsaus-public-scanner/actions/runs/40316862372
- Created 2026-10-26T11:40:53Z, completed with conclusion `success`.
- Run branch: `research/offline-technical-risk-20261021`.
- GitHub API `/actions/runs/40316862372/artifacts` returned
  `{"total_count":0,"artifacts":[]}` at this checkpoint.
- No frozen OHLCV snapshot or OOS candidate JSON was recovered from this run.

## Existing workflow, do not duplicate

`.github/workflows/candidate-feature-oos-report.yml` on the older research
branch already:
1. Runs historical OOS research from daily OHLCV data;
2. Saves `reports/candidate_feature_oos_input_snapshot.json`;
3. Replays from that exact snapshot and checks candidate/portfolio output and source hashes;
4. Publishes `candidate-feature-oos-historical-report` with candidate,
   quarterly, and frozen-input JSON.

Its trigger is `workflow_dispatch` or selected older-branch file pushes.
Do not confuse historical CI success with an accessible, independently
verified historical dataset. Do not invent the missing 96-trade source.

## Next evidence-producing action

Prefer a new execution of the **existing** historical workflow on the older
research branch (manual dispatch after explicit branch/run review), then
retrieve its fresh artifact, record run ID, SHA, source metadata and per-file
SHA256, verify snapshot replay, and feed the resulting candidate pool into
the isolated source-bound tranche bridge. Preserve source licensing and
distinguish Yahoo source replay from independent quote validation.

This document alone does not trigger a workflow, retrieve OHLCV, validate
alpha, merge a branch, modify the live scanner or place orders.
