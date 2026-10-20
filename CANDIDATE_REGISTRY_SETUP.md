# Private candidate registry: setup and limits

This is a **shadow-only** audit. It neither changes trades nor delivers alerts.

Configure the GitHub Actions repository secret `SCANNER_CANDIDATE_REGISTRY` using private JSON. Example with fictional symbols:

```json
{"schema_version":1,"candidates":[
  {"id":"nomination-001","symbol":"SYNTHETIC_A","status":"ACTIVE","monitor_mode":"MANUAL"},
  {"id":"nomination-002","symbol":"SYNTHETIC_B","status":"REGISTERED","monitor_mode":"DISCOVERY"}
]}
```

Include **all** user-nominated tickers, not only those already present in scanner configuration. Keep stable IDs. Use `CLOSED` or `INVALIDATED` with `closure_reason` for explicit removals. Never commit the real list or disclose it in public Actions logs, PRs, or issues.

A `MANUAL` nomination is compared with the hydrated primary and supplemental manual-watch configurations. A `DISCOVERY` nomination is **unverified** until individually matched to actual EU/US discovery execution. Aggregate market scans do not prove a specific nominated ticker was checked. `complete=true` does not prove quote freshness, notifications, or phone delivery. Missing or invalid registry means unavailable, not zero missing. Public CI tests use synthetic data only.

Rollout: (1) privately reconcile the full authoritative nomination list; (2) set the repository secret under Settings > Secrets and variables > Actions; (3) inspect aggregate-only `CANONICAL_CANDIDATE_COVERAGE` on a trusted run; (4) separately verify discovery routing, data freshness, and notification delivery; (5) keep PR #56 draft until these checks pass. Never copy the secret into public CI.

## Evidence levels (do not conflate)

1. **Registered:** the authoritative private nomination exists.
2. **Configured:** a MANUAL nomination is found in hydrated manual watch configuration. This is **routing evidence only**, not proof of a completed market check.
3. **Observed:** the runtime's manual report contains a recent per-symbol check, an explicit data blocker, or a justified deferral; missing or stale observations remain overdue.
4. **Delivered:** a notification is confirmed at its delivery destination. Neither the canonical configuration audit nor public CI establishes this.

`CANONICAL_CANDIDATE_COVERAGE complete=true` refers only to **registration-to-configuration reconciliation** for manual candidates, and only when there are no discovery nominations pending verification. Never describe it as full end-to-end monitoring or successful alert delivery.
