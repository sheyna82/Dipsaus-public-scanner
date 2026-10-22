# Candidate free multi-equity research source (not yet ingested)

Inspected upstream repository:
https://github.com/stefan-jansen/machine-learning-for-trading/blob/main/data/equities/market/us_equities/README.md

Upstream documents NASDAQ Data Link WIKI/PRICES, 1962-01-02 to
2018-03-27, about 3,199 US tickers including delisted companies,
approximately 650 MB parquet, and **free API-key registration required**.
It is frozen after March 2018, and is NOT a source of current signals.

Important distinctions:
- This is a candidate, not data already downloaded or validated.
- 'Includes delisted issuers' does not by itself prove every historical
  universe, delisting return, corporate action, or benchmark adjustment
  is correctly represented.
- Audit adjusted OHLC vs raw OHLC and dividend/split handling.
- Audit license/redistribution terms before storing any dataset.
- Test ticker/date coverage, survivorship, as-of membership, delisting,
  and missingness before computing performance.
- Freeze scoring, sample inclusion, holding period, fees and downside
  thresholds BEFORE inspecting a genuinely independent holdout.
- No credentials or bulk licensed datasets should be committed to
  public GitHub. Free-only; no paid subscriptions.
- Run entirely as separate offline research. Do not modify live alerts.

Next implementation step: add a local-only importer for a bounded,
schema-validated subset of this source (or equivalent legally
redistributable dataset), with explicit adjustment provenance and
benchmark compatibility. A downloadable source is not proof of
reproducibility or predictive power.
