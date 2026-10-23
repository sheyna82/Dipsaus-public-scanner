# Historical data source feasibility — research only (2026-10-23)

No provider has been authenticated or downloaded in this research. This document is a due-diligence shortlist, not a claim of predictive validity.

## Candidate sources

- **Nasdaq Data Link WIKI/PRICES**: public-domain historic US equities, frozen in March 2018. Nasdaq explicitly warns it is unsupported and not recommended for investment or analysis. Potentially useful as a *historical methods demonstration*, not a contemporary trading universe. Verify delisted coverage, timestamp conventions, and split adjustments before use. Source: https://data.nasdaq.com/databases/WIKIP
- **Stooq**: historical daily prices for several markets. Reported personal-use restrictions and automated-download barriers. Do not scrape, redistribute or integrate into public CI without direct terms and permission verification. Source: https://stooq.com/
- **Sharadar Equity Prices (Nasdaq Data Link SEP)**: extensive adjusted/unadjusted US history and corporate actions, but premium; not suitable for a free-only implementation. Source: https://data.nasdaq.com/databases/SEP/documentation
- **ohlc.io**: advertises a free tier with only seven US symbols and five years of history, plus point-in-time/as-of functionality. Independently verify provider terms, historical replay guarantees, and data accuracy before use. Limited universe cannot support broad stock discovery validation. Source: https://ohlc.io/data/historical-stock-prices

## Non-negotiable acceptance criteria

1. Permission for intended research use, automated retrieval, retention, and CI; never store API keys in the public repository.
2. Explicit market calendar, timezone, raw vs adjusted OHLCV, splits, dividends and delisting policy.
3. Historical *availability* timestamps and reproducible snapshots; do not infer publication/ingestion timestamps from price bar dates.
4. Point-in-time eligible security universe, including delisted instruments; account for ticker changes and identifier reuse.
5. Immutable source/version manifest and content hashes; provider provenance must be independently checked.
6. Chronological train/validation/untouched holdout split with label embargo and no tuning on final holdout.
7. Baseline vs ATR comparison using Brier score, log loss, uncertainty estimates, costs and slippage; report number of securities and market regimes.
8. Do not label outcomes as verified, independent, or trade-ready solely because synthetic regression tests pass.

## Next executable research milestone

First obtain a small **licensed and independently inspectable** historical sample (including at least one delisted security and corporate action), document exact data access terms and timestamps, and run a reproducible offline ingest audit. Do not introduce a network fetcher or claim out-of-sample predictive edge before those prerequisites are met.
