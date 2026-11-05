# US independent recovery setup: upstream evidence gap (2026-11-02)

Status: VERIFIED CODE AUDIT; NOT VERIFIED as live setup recognition. Research only.

## Reproduced baseline
- PR regression run 41514897521: 1,343 tests OK after commit 0a6fbe99aad862cb74faaf7c84e578e3c9a478ea.
- The regression exercises existing notification lifecycle; it is not prospective evidence that a new independent recovery setup is recognized.

## Existing implementation, do not duplicate
- `private_notifications.py` already accepts `verified_setup_id` only with `independent_setup_verified is True`, `provider_freshness_pass is True`, `structure_available is True`, and an allowed 1-64 character identifier. Otherwise it falls back to legacy phase dedupe.
- `manual_recovery_trigger_watch.py` builds intraday observations from a single 1-minute provider snapshot: fresh quote, higher low across two halves of a 12-bar window, median-close reclaim, rebound, breakout/hold. It does **not** emit `verified_setup_id` or `independent_setup_verified`.
- `us_live_trigger_routes.py` promotes research routes by existing quality gates; it does **not** establish independent setup identity.

## Critical boundary
A changed price, elapsed day, ticker, new route, fresh data, or a repeated 12-bar higher-low observation does not prove an independent setup. In particular, a rolling 12-bar window may label the same recovery leg repeatedly.

## Research-only acceptance contract for a future detector
1. Work from chronologically ordered, timestamped bars with explicit provider provenance and a frozen data snapshot; reject missing, stale, non-monotonic, duplicated or contradictory bars.
2. Define the previous setup's structural low, confirmation pivot, invalidation and active/released lifecycle using **only bars available at each decision time**.
3. Permit a new candidate setup only after independent reset/rebase evidence distinct from the prior active leg. A new day or a rolling-window shift is insufficient.
4. Require multiple observations across time (including a persistent higher low/reclaim), with predeclared thresholds and explicit cooldown; verify against overlapping-window false positives.
5. Make IDs deterministic and stable for replay; never use current clock time, price alone, random identifiers or an arbitrary free-text label as identity.
6. Keep `independent_setup_verified=False` until independent reset evidence is proven. Do not populate `verified_setup_id` from an unverified route or manually inferred watchlist.
7. Evaluate with synthetic adversarial sequences, snapshot replay, no-lookahead prefix invariance, and out-of-sample historical episodes; report false new-setup rate and missed distinct setups.
8. Keep notification eligibility, broker bid/ask, news/earnings, R/R and portfolio capacity as **separate gates**. Setup verification is not a buy signal.
9. No live ntfy calls, broker orders, private repository writes or production/main changes during research.

## Current conclusion
Notification dedupe is regression-tested; upstream independent setup recognition remains NOT VERIFIED. Do not claim CSGP is monitored for independent new setups until a detector, replay evidence and operational integration are separately demonstrated.
