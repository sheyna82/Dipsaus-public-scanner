# US selection-effectiveness — real-data feasibility checkpoint (18 Nov 2026)

Scope: isolated research branch only; source-code audit, **not** live source verification.

## Decision: no defensible measured missed-opportunity rate yet

The current US discovery feed is **Yahoo chart history**, not Massive. Source audit in `research/us_external_evidence_plan_20261117.md` traces `safe_runner.py us` to `us_recovery_pilot.py` and `us_momentum_recovery_discovery.py`. The Massive normalizer is a separate offline fixture experiment. Do **not** infer that a working Massive adapter implies a live Massive entitlement or live US scanner feed.

Current historical private reports contain the original research selection and limited price context; they do not independently attest the *subsequent* completed bars, retrieval times or broker quotes. Thus a valid denominator for *profitable missed opportunities* is unavailable.

## Concrete real-data bridge

1. At the **original decision**, preserve a private immutable snapshot with symbol, exact observation/decision times, historical close, historical friction, source response digest, provider identifier, session date and adjustment policy. Missing timestamps remain missing; never substitute report-generation time.
2. **After** that decision, capture completed OHLCV bars privately from an authorized source, retaining both the provider's bar start/end semantics and the *actual retrieval/observation time*. A retrospective Yahoo download today does **not** prove the bar was available at an earlier decision time.
3. Verify market session and early-close boundaries against an independent official calendar; resolve splits, delistings, symbol changes and dividends consistently. Never fabricate the completed-bar end by simply adding 24 hours to a daily bar's start timestamp.
4. Run `research/us_strict_forward_evidence_20261118.py` with actual completed-bar end and observed timestamps. The separate `us_aggregate_forward_bridge_20261118.py` can adapt normalized Massive fixtures only when matching completion receipts exist. It is **not** wired to the live Yahoo feed.
5. Retain the independent receipt/pin privately; hash self-consistency and self-declared verification fields do not establish provider authenticity or timing. Public repo receives **code and synthetic fixtures only**, never private candidate IDs or raw licensed data.
6. Compare the rejected/pending/overflow cohorts with evaluated candidates at a fixed 5–15 trading-day horizon. Report censoring, missingness and sample sizes; do not equate breakout/retest pattern with a profitable executable trade.
7. For a genuine opportunity comparison, add actual bid/ask, account-specific DEGIRO route, FX, spread, fees, liquidity, news/events, invalidation and target. Keep R/R >=2 and projected net EUR >=150. No automatic orders.

## Important interpretation

- A post-snapshot breakout/retest is an **observed technical pattern**, not a verified missed buy.
- `historical_friction_usd` is a *reference*, not independently confirmed resistance.
- The current offline tests establish software behavior on synthetic data, not predictive accuracy or trading performance.
- An independently anchored receipt must be verified by an actual external trust boundary; a caller-provided `independent_verification=True` is not proof.
- No public live probe or CI artifact should contain licensed market data or private account information.

## Next acceptance gate

Before any empirical success-rate claim, obtain **one** privately held, authorized end-to-end case: original time-stamped selection; at least one subsequently observed completed bar with independently verified session boundaries; and a private, verifiable capture receipt. Then run the same process on a non-cherry-picked cohort, including non-events and censored candidates. No production wiring is authorized.
