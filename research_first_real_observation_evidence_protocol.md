# DIPSAUS — first real observation: evidence acceptance protocol

Status: **research-only; NOT an operational scanner integration**.

## What exists
- Manual intake accepts caller-supplied `observation.json` and exact `source.bin`.
- It checks schema, local clock ordering, byte digest, immutable candidate identity,
  and archives both the candidate and source bytes.
- GitHub CI validates this mechanism with **synthetic** fixtures only.

## What the current chain cannot establish
1. A supplied URL does not prove the bytes came from that URL.
2. A caller-supplied `source_observed_at_utc` is an assertion, not an
   independently verified observation timestamp.
3. A GitHub artifact created later cannot retroactively prove the candidate
   existed before the market move.
4. Passing the research tests says nothing about signal precision, expectancy,
   drawdown, capital efficiency, or suitability for a live order.

## Minimum evidence required for the first real observation
- Record the exact source provider, endpoint, symbol, exchange, market session,
  provider response bytes, response receipt time, and provider terms.
- Preserve an independent server-side receipt tied to the candidate digest
  **before** any outcome window begins. Verify the artifact bytes against the
  candidate and source digests; receipt metadata alone is insufficient.
- Record selection rule and candidate universe **before** observing outcomes.
  Record all candidates and rejections to avoid cherry-picking.
- Mark each provenance or timing claim as **unverified** unless an independent
  verification method actually exists.
- Keep source capture separate from offline processing. The existing
  `research_public_https_source_capture.py` must NOT be used for live capture:
  its injected opener is not a connection-pinned, audited production transport.
- Never place API keys, private account data, or licensed market-data dumps in
  the public repository or public artifacts without explicit permission.
- Do not connect the manual intake to the operational scanner, cron, ntfy,
  or private repository without separate authorization.

## Acceptance criteria for a prospective study
- One actual, timestamped observation is **not** strategy validation.
- Each signal needs immutable registration, exact inputs, selection criteria,
  reproducible later outcomes, costs, and benchmark comparisons.
- Analyze out-of-sample performance and portfolio capacity, 5/10/15-day exits,
  MAE/MFE, time-to-recovery, capital lock-up, and opportunity cost.
- Trade readiness remains **false** until independent evidence and a separate
  decision process justify any operational change.

## Next actionable work
Identify a legally reusable market-data source and independently verifiable
server-side receipt method. Implement and audit network transport in isolation;
then capture and register the first actual candidate **before** its outcome.
