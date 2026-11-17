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

## Provider terms review — primary-source desk research, 2026-11-17

Sources reviewed:
- Massive Market Data Terms, updated 2026-11-03: https://massive.com/legal/market-data-terms-of-service
- Massive redistribution guidance: https://massive.com/knowledge-base/article/how-can-i-redistribute-massives-market-data
- Massive stock API overview: https://www.massive.com/stocks

Findings from provider-published material (not account-specific attestation):
- Individual access is for the subscriber's own personal, non-business research/investment activity, subject to provider and exchange conditions; this does not automatically authorize data sharing, public repository artifacts, third-party display or a commercial product.
- Publishing raw prices/charts or making data accessible to others generally requires explicit commercial redistribution rights. Even derived signals can require an entitlement assessment depending on the information revealed.
- Massive describes stock-data feeds and historical/real-time tiers, but **no account plan, API key, entitlement, exchange classification or live access has been verified here**.
- A GitHub Actions secret, if one exists, is not evidence of licensing, source independence or permitted publication. Never print a secret or place raw licensed market data in a public CI log or artifact.

Required decision before implementing a network client: establish the actual account's access tier and whether personal automated research and any intended notification content are covered; choose a private execution/storage boundary for licensed data. No public-repo live feed integration is approved by this dossier.

## Existing repository provider inventory — source audit, 2026-11-17

The public repository already contains provider-oriented code; adding a second unrelated credential workflow would duplicate risk:

- `us_company_profile.py` reads `FINNHUB_API_KEY` from the environment and fetches Finnhub issuer profiles. Its own result is `PROFILE_RESEARCH_AVAILABLE` / `UNVERIFIED`, **not independently verified OHLCV or broker pricing**.
- `source_audit.py` probes Nasdaq Trader symbol-directory text files, Stooq daily CSV and Yahoo chart history. It explicitly declares `SOURCE_TEST_ONLY`, `actual_symbols_screened=0`, `full_us_scan_executed=False`, `trade_ready=False`. Reachability is not entitlement, live-feed correctness or permission to republish.
- `migration/ACTIVATION.md` is **historical and explicitly not a live status report**. It lists provider secret names `FINNHUB_API_KEY` and `EODHD_API_TOKEN`, private state storage and notification safeguards; it does not prove those secrets are currently installed, valid or entitled.
- GitHub code search on the default branch found references to `FINNHUB_API_KEY`; no account secret values were inspected or exposed. Search results do not prove the absence of other providers.

**Next safe research task:** trace the current US scanner's existing provider selection, private report boundary, and exact freshness/fallback semantics from source and recent successful *non-sensitive* job metadata. Determine whether an existing authorized private research path can be reused before proposing Massive credentials. Never trigger a live probe that logs raw licensed data into public CI.

## US workflow boundary audit — 2026-11-17

Inspected current branch copies of `.github/workflows/shadow-us.yml`, `.github/workflows/research-finnhub-manual-observation.yml`, `us_news_fallback.py` and `migration/workflows/us.yml`.

- **Scheduled US workflow**: `shadow-us.yml` runs `safe_runner.py us` on a public repository with secrets for Finnhub, EODHD, private state and notifications, but explicitly sets `SCANNER_NOTIFICATIONS_ENABLED: 'false'`. It specifies no public artifacts or report summaries. This is source-level configuration, not proof that the run accessed valid licensed data or delivered a signal.
- **Finnhub use**: `us_news_fallback.py` accesses company-news and earnings-calendar with a token in the `X-Finnhub-Token` request header, timeout 15 seconds, and returns incomplete research context. This is **not a live OHLCV quote source**.
- **Separate manual Finnhub observation**: `research-finnhub-manual-observation.yml` explicitly uploads a source-response JSON file as a public GitHub Actions artifact retained seven days. The comment describing the response as 'public market data' is **not legal authorization to redistribute it**. Its exact content and entitlement need independent review; do not trigger or copy this workflow into the new US research path.
- **Observed recent US run metadata**: GitHub Actions run `44098411475`, created 2026-11-17 14:00:17 UTC on `main`, concluded `success`. This establishes a successful workflow execution only; no claim about data freshness, symbol coverage, broker verification or signals.
- **Safety consequence**: keep the new US research workflow entirely offline, without provider secrets, uploads, notifications or production calls. Any live integration must have a private data boundary and separate entitlement approval.

**Open questions**: Which provider supplies current US OHLCV inside `safe_runner.py us`? Are its historical and real-time entitlements sufficient? Does the private state contain provider provenance and expiry? These require a focused call-graph audit, not inference from a green Actions badge.
