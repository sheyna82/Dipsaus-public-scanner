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

## Verified provider constraints (2026-10-23)

Official Sharadar terms at https://sharadar.com/terms permit individual personal non-professional use, but **prohibit redistributing the data or derivatives permitting reconstruction**. Consequently, do not commit Sharadar sample OHLCV to this public repository, publish raw downloaded samples as GitHub Actions artifacts, or assume a personal API key may be used for a public shared data service. A private local, license-compliant test may be possible subject to account terms.

Official Sharadar website at https://sharadar.com/ advertises a free entry-level dataset covering the Dow 30 and a sample at https://sharadar.com/sample. Nasdaq SEP documentation at https://data.nasdaq.com/databases/SEP/documentation specifies free example tickers for **2018-09-01 through 2018-12-31**, with API-key authentication; this is a limited example, not evidence of current market-wide coverage. Nasdaq states SEP OHLCV is split/stock-dividend adjusted and separately supplies unadjusted close, so any imported series must document its actual adjustment basis.

**Current decision:** Do not download, publish, or claim validated historical predictions until legitimate access is established. The public repository may hold only the ingestion code, synthetic test fixtures and non-sensitive aggregate evaluation metrics that are permissible under the applicable license. A license-compliant local run can produce audit summaries without uploading licensed price rows.

## New candidate: Kaggle CC0 historical US stock dataset (2026-10-23)

Dataset page: https://www.kaggle.com/datasets/borismarjanovic/price-volume-data-for-all-us-stocks-etfs

The uploader marks **Huge Stock Market Dataset** as **CC0 / Public Domain** and explicitly says users may do as they wish with it. This is a substantially more practical *open-licensed historical research candidate* than personal-use-only feeds. The page describes ~8,539 CSV files of US stocks and ETFs, last updated in November 2017, with columns Date, Open, High, Low, Close, Volume, OpenInt. It says historical prices were adjusted for dividends and splits. These are the uploader's representations, **not independent confirmation of underlying upstream data rights or accuracy**.

**Safe integration proposal:** first download through Kaggle's official interface with authorized access, then inspect the actual files and upstream provenance. Keep downloaded data out of public CI pending independent source-rights checks. Convert individual CSVs locally into the canonical lower-case six-column schema; preserve source files, ticker identity, adjustment assumptions, and original checksums in a local-only manifest. The current importer will reject raw Kaggle files because their headers and extra OpenInt column differ: do not silently drop or reinterpret fields without a separately tested converter.

**Important scientific limits:** frozen 2017 data cannot validate modern scanner performance; membership of the historical universe, delisting, survivorship, adjustments and true historical data availability remain unverified. The sample may serve as a genuine-price engineering and retrospective methods test, but cannot alone establish a point-in-time predictive edge. No dataset was downloaded or processed as part of this note.
