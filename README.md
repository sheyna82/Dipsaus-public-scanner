# DIPSAUS public scanner

Clean source-only migration of EU and US recovery research and fast PRE-ALERT monitoring.
No private Git history, holdings, acquisition prices, personal watchlists, notification identifiers or runtime reports are included.

**Migration status: active public production scanner.**
The approved handover completed on 2026-10-09. EU, US and market-hours PRE-ALERT shadow runs passed, followed by an exclusive live PRE-ALERT run. All original private workflows are disabled and their last notification ledger was synchronized privately. PRE-ALERT is started through workflow_dispatch by an external scheduler. The built-in PRE-ALERT cron trigger has been removed to prevent competing pending runs. Each dispatch performs one check. Live workflow concurrency and the private notification ledger prevent overlapping senders and duplicate delivery. Read-only tests use independent concurrency and neither save runtime state nor send notifications. External dispatch does not guarantee immediate GitHub runner availability; EU and US discovery retain their schedules. Standard public GitHub-hosted runners are required. Personal configuration and runtime reports remain private. Manual PRE-ALERT dispatch defaults to notifications off; live dispatch uses the exclusive sender guard.

## Validation

Python 3.12 on Linux:

```
python -m pip install --require-hashes -r requirements.lock
python -m unittest discover -p 'test*.py'
```

49 regression and migration safety tests passed in GitHub Actions, including inherited recovery/execution tests, fresh/stale provider handling, private-state visibility, notification deduplication and suppression of personal subprocess output.
Pinned Python dependencies were checked with pip-audit: no known vulnerabilities reported at preparation time. This is not a guarantee against unknown vulnerabilities.

## Trading behavior

Keep recovery discovery separate from execution. Preserve early turns, fresh provider checks, EU research, market-wide US momentum discovery and seven rotating deep batches per US sweep. A full 21-batch rotation spans three sweeps. Fast PRE-ALERT checks remain separate from expensive discovery scans. Missing/stale data stays DATA-BLOCKED, never a negative setup conclusion.

No automatic orders. Entry still requires independent broker bid/ask/spread, current recovery-leg invalidation, confirmed bottom, day/week review, first friction, meaningful resistance and realistic further recovery zone, R/R >=2, meaningful gross EUR profit, risk budget, news/events, FX and portfolio fit. An add requires a new standalone setup; never average down merely to lower cost. Profit/exit and fast-crash monitoring retain their existing signal logic.

## Private runtime

Sensitive settings come only from GitHub Secrets. Scanner stdout/stderr are suppressed. No personal summary, artifact, cache or public Git commit is produced by the replacement workflow templates. Runtime reports and cooldown state are stored via the GitHub contents API in a verified **private** state repository. These API writes do not run private Actions workflows; all private workflows must be disabled before public notifications can be enabled.

The state token needs contents read/write and Actions read on the selected private repository. Do not put it into code. A missing or invalid state blocks the scan rather than resetting cooldowns. Notification delivery is reserved before sending: uncertain delivery is not automatically retried and requires private inspection, preventing duplicate pushes.

See `migration/ACTIVATION.md` for the controlled cutover and outstanding checks.
