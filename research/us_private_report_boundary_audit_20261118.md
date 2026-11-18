# US real-report capture boundary audit — 18 November 2026

Read-only inspection of the **private** repository `sheyna82/Dipsaus-scanner`, `main`; no production changes or workflow execution. This public research note contains **no candidate names, prices, reports, credentials or account details**.

## Confirmed code behavior

- `us_recovery_pilot.py` retrieves Yahoo 6-month daily charts and converts each timestamp to a UTC **date**, losing the original instant and provider retrieval time in the emitted rows. That date cannot establish when the closing bar was complete or observable.
- `us_auto_prealert_handoff.py` combines deep-recovery and momentum candidates and writes `reports/us_auto_prealert_candidates.json`. It preserves `last_bar_date` for deep candidates and a `historical_close_usd` reference, but does not write an independently attested per-candidate `decision_observed_utc`, `source_last_bar_utc` or raw response receipt. `generated_utc` is the report creation time only.
- The same handoff script prints the **entire** JSON report to stdout. `us_live_trigger_routes.py` also prints the entire routes JSON, including watchlist membership. Consequently the existing workflow's logs may expose research candidates even if no artifact is uploaded.
- The private `.github/workflows/us-recovery-pilot.yml` uploads batch, momentum, handoff and routes JSON as an Actions artifact and prints candidate symbols and reference prices in its job summary. Repository privacy and artifact retention do not independently establish market-data redistribution rights or an immutable timestamped evidence receipt.
- The workflow publishes routes to `config/us_live_trigger_routes.json` on private `main`. **Do not change or invoke this workflow for research**.

## Operational decision

The existing report artifacts can support an **exploratory selection-funnel audit** (cohort membership, deep-dive capacity, missing fields), but not an independently verified point-in-time missed-trade rate. A report's `generated_utc` must not be relabeled as a candidate decision or bar observation timestamp.

Do not download private artifacts into public CI, commit them, echo their symbols or prices into public logs, or publish raw provider responses. Do not claim private Actions artifact existence implies a legally authorized external source capture.

## Smallest safe future empirical step

1. In a **separately approved private research boundary**, capture the source's original timestamp semantics, actual retrieval time, response digest, adjustment policy, session calendar and immutable original decision record. Ensure logging is redacted and storage access/retention approved.
2. Preserve all enrolled candidates, including overflow, technical rejects and non-events, **before** any future outcomes are seen.
3. Collect post-decision completed bars with provenance receipts; verify the session close and early-close calendar independently. Do not infer completion from a daily date alone.
4. Run the already isolated offline `us_strict_forward_evidence_20261118.py` and `us_prospective_cohort_accounting_20261118.py` privately on that authorized dataset. Export only aggregate counts, sample sizes and missingness if disclosure is permitted.
5. Separately assess executable net EUR profit and R/R from broker and costs; a breakout pattern is not a trade.

## Acceptance state

- Existing real-data cohort and provenance evidence: **NOT VERIFIED**.
- Public isolated synthetic test status: **329/329 green** (Actions run 44263945471).
- No production modification, no workflow dispatch, no order or notification.
