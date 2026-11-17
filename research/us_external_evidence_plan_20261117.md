# US shadow — external evidence acceptance dossier (2026-11-17)

Scope: isolated research branch only. No production integration, notifications or orders. This dossier records **unmet requirements**, not completed attestations.

## Verified from branch source

- `us_massive_pipeline_20261117.py` explicitly accepts **synthetic offline fixtures**, labels the source `massive-offline-fixture`, and always returns `provider_independently_verified=False`, `exchange_calendar_verified=False`, `trade_ready=False`.
- `us_source_identity_20261117.py` validates source metadata syntax only; a valid URL, digest, license reference, or MIC does **not** prove provenance, licensing or official instrument identity.
- `us_exchange_calendar_evidence_20261117.py` checks metadata but never attests an official trading session.
- `us_net_trade_20261117.py` consumes broker, FX and cost dictionaries containing `verified=True` flags. Those flags are **self-declared inputs**, not independent DEGIRO account/route verification.
- `us_shadow_decision_20261117.py` unconditionally blocks source independence, official calendar and data license and returns `trade_ready=False`, `notify=False`, `automatic_orders=False`.

## Evidence work required before a real US candidate alert

1. **Provider provenance and rights** — choose an authorized market-data provider; obtain primary-source API documentation, entitlements and permitted display/redistribution terms; fetch an actual response via a bounded, credential-safe research client; store retrieval timestamp, response digest and immutable source reference. A SHA-256 match alone is insufficient.
2. **Independent cross-source check** — obtain a second *independent* source or official exchange reference for ticker, ISIN, listing MIC, currency, split policy, price/time consistency and corporate actions. Document tolerances and conflict handling; ambiguous ticker/ISIN mapping blocks.
3. **Official exchange calendar** — obtain dated primary-source NASDAQ/NYSE session/holiday/early-close evidence. Verify the requested market, session date, clock and bar boundaries. Metadata supplied by the same feed is not independent confirmation.
4. **DEGIRO execution route** — independently establish the actual tradable instrument, venue, account availability, bid/ask freshness, order currency and complete route-specific commissions/FX. Public fee schedules alone are not account-specific execution proof.
5. **Candidate quality** — obtain timely news/events, liquidity/spread, multi-timeframe technical levels, invalidation, portfolio concentration and EUR net return. Require R/R >= 2 and expected net profit >= EUR 150 under conservative costs and spread.
6. **Reproducibility and operational safeguards** — redact credentials, pin dependencies, document rate limits, timeouts, error budgets and evidence expiry. Distinguish live source validation from synthetic unit tests. Keep all decisions fail closed.

## Explicit non-goals

- No automated orders, no auto stoploss/stoplimit.
- No claim that offline regression success establishes live-market correctness.
- No promotion to production or draft PR #65 without separate approval and independent acceptance evidence.

## Suggested implementation sequence

A. Read-only, credential-safe provider probe with a clearly labeled **live research** output and no notification path.

B. Official session calendar retrieval and source-citation record.

C. Independent instrument identity cross-check with explicit ticker-versus-ISIN semantics.

D. Broker route and EUR net calculation audit with actual account-specific evidence.

E. End-to-end dry-run report containing exact missing evidence and blocking reasons; only then discuss a separate manual alert-approval process.

Status as of this dossier: **all A–E are pending**. Offline CI success does not close these items.
