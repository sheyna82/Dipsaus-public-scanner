# DIPSAUS — next real observation: manual research runbook

Status: manual only. No new market-data automation is authorized. This guide does not place orders or alter notifications.

## 1. Collect
1. Open [manual Finnhub research workflow](https://github.com/sheyna82/Dipsaus-public-scanner/actions/workflows/research-finnhub-manual-observation.yml).
2. Select **Run workflow**, branch **main**, and one of the currently allowed research symbols (AMD, COHU, CSGP, AAPL). Start one manual run. The workflow checks out its own pinned research implementation.
3. Wait for the job to finish successfully. A green unrelated CI run is not evidence of an observation.
4. On that exact run, download the artifact named `dipsaus-finnhub-research-observation` before its seven-day expiry.

## 2. Preserve and verify
1. Record the workflow run ID, artifact ID, run time, chosen symbol, ZIP SHA-256, internal JSON SHA-256 and source-byte SHA-256.
2. Verify the ZIP and source observation with the offline modules before any aggregation. Reject mismatches and duplicate windows.
3. Preserve the original ZIP outside the expiring Actions artifact. Do not commit secrets or private account data. Publishing market-source bytes to a public branch requires an explicit review of contents and provenance.
4. Do not overwrite the existing AMD observation. Append distinct records only, with their own immutable receipts.

## 3. Interpret
- A second quote taken on the same UTC date does not establish multi-day coverage.
- The existing 20-observation / 5-day threshold is a software coverage smoke test, **not** evidence of trading edge.
- A quote is not a registered candidate. Do not label it a buy signal.
- Independently verify market source and timestamps, then pre-register candidate rules and outcomes before making performance claims.

## Current verified evidence
- AMD observation, 2026-11-03, run 41712197672, artifact 13268535597, preserved in `research-evidence/amd-20261103-source-observation.json`.
- 1 distinct observation, 1 UTC day, 1 symbol.
- No independent price authentication or prospective trading outcomes.

## Constraints
No changes to `main`, operational scanner, ntfy, cron, API keys, automatic orders or automatic market collection are authorized by this document.
