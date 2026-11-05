# DIPSAUS prospective market-evidence protocol (research only)

Status: **protocol drafted; prospective trading evaluation NOT started**. Date: 2026-11-03.

## Distinguish four evidence levels
1. **Raw source observation**: captured provider bytes, timestamp, hashes, and immutable archive. Does not authenticate the provider or prove quote accuracy.
2. **Verified market observation**: independent source comparison with documented timestamp tolerance, venue, currency, session and adjusted/unadjusted conventions. Differences and missing data are retained, not silently corrected.
3. **Pre-registered candidate**: symbol, rule/version, universe, scan timestamp, entry convention, planned horizons, benchmark, costs and risk exclusions fixed *before* observing the outcome. A quote alone is not a candidate.
4. **Prospective outcome**: later prices and corporate actions independently verified; realized hypothetical return and capital-days calculated for all candidates, including failures and missing data. No trading authorization follows automatically.

## Initial observation design
- The existing manual Finnhub workflow allows only AMD, COHU, CSGP, AAPL. Do not expand the allowlist or automate scheduling without separate authorization.
- The offline 20-observation / 5-UTC-day coverage gate is a **technical smoke-test threshold only**. It cannot establish statistical power, market independence or edge.
- Retain each original ZIP and raw response, GitHub run/artifact ID, content SHA-256, source clock and ingestion clock. Export must be write-once; never overwrite a prior record.
- Publish no API keys or non-public account/portfolio information. The research branch must remain separate from main and the operational scanner.

## Before prospective strategy claims
- Fix a versioned candidate-selection rule, benchmark (e.g. broad index and matched sector), next-session execution convention, commissions, spread/slippage, FX assumptions and 5/10/15-session horizons.
- Record all eligible and rejected candidates; no cherry-picking of symbols or dates after outcomes become known.
- Prevent look-ahead, survivorship, overlapping-window and repeated-measurement leakage; aggregate by independent dates and market regimes.
- Compare net returns, drawdown, MAE/MFE, time-to-recovery, capital-days and opportunity cost against simple baselines. Report uncertainty intervals and negative quarters.
- Require sufficiently broad out-of-sample data and independently verified outcomes before proposing operational integration. A positive small sample is exploratory only.

## Current evidence inventory
- One original AMD observation from GitHub run 41712197672, artifact 13268535597, with source JSON preserved on the isolated research branch.
- Original ZIP retained in a separately downloadable local preservation bundle; ZIP bytes not stored in GitHub source tree.
- No verified multi-day series, independently authenticated prices, pre-registered trading candidates, or prospective outcomes established by this record.

## Stop conditions
If source hashes mismatch, provider provenance cannot be independently checked, timestamps are ambiguous, corporate actions are unresolved, or the evaluation rule was selected after seeing outcomes, mark the relevant evidence inconclusive and do not promote it to a trading recommendation.
