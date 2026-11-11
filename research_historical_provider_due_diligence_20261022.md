# Historical data-provider due diligence — 2026-10-22

Research-only, **not** an endorsement, purchase, verified dataset, or completed backtest. No live changes.

## Observed GitHub source probe

The 5-year Yahoo chart probe returned structurally acceptable OHLCV for 11 surviving issuers (XOM, JPM, JNJ, CAT, PG, NEE, AMT, LIN, DIS, HD, MSFT) after excluding the current exchange date. DIS had one inconsistent OHLC observation on the still-current date 2026-10-22; 1,254 earlier bars passed the structural check. Delisted LEH returned HTTP 404. This does not prove Yahoo lacks *all* delisted stocks; it proves **this requested ticker** was unavailable through **this endpoint**. None of these prices has independent corporate-action verification.

## External source candidates to assess

1. **CRSP / WRDS** — CRSP describes active/inactive US security coverage, permanent PERMNO/PERMCO identifiers, corporate actions and delisting data. Strong methodological reference, likely institutional licensing/access. Docs: https://www.crsp.org/research/crsp-us-stock-databases-2025-layout/ and https://wrds-www.wharton.upenn.edu/demo/crsp/form/ . **No access or dataset obtained.**
2. **Sharadar-based reproducible cleaning project** — third-party GitHub project claims to rebuild a survivorship-clean panel with ticker-recycling and adjustment safeguards. Inspect license, provenance, point-in-time validity, actual artifact availability and permission independently before reuse: https://github.com/tenicho/data-cleaning . **Claims not verified; no dataset obtained.**
3. **FinzData** — vendor advertises delisted history, but marketing coverage and pricing are not independent validation. https://finzdata.com/historical-stock-data . **No dataset obtained.**
4. **HistoricalData.net** — advertises delisted histories and discusses missing index constituents, terminal proceeds and identity boundaries; sample availability is not comprehensive universe coverage. https://historicaldata.net/survivorship.html . **No dataset obtained.**
5. **Confirmed earnings release timestamps** — earningscalendar.net documents confirmed events from 2020, including a press-release publication date. Historical *event date* is not automatically historical *knowledge date*: preserve publication timestamp and as-of availability. https://api.earningscalendar.net/documentation . **No API key or records obtained.**

## Acquisition gate before preregistered full-score evaluation

- Obtain lawful licensed local snapshots with an immutable source manifest and checksums; never publish proprietary price data or API keys in this public repo.
- Confirm historical security identity and membership *as of each sample date*, delisted issuers, ticker reuse, splits, dividends, delisting outcomes and missing bars.
- Confirm earnings **announcement-date information known at signal time**, not merely realized earnings dates retroactively backfilled.
- Verify independent benchmark alignment, exchange calendars, sector membership and costs.
- Freeze eligible cohort, rules, development/validation/test dates and 10-session embargo **before** reading the final holdout.
- Report exclusion counts and delisted-vs-survivor sensitivity. Do not imply statistical significance from eleven surviving stocks or from source-availability success.

**Current decision: DATA_BLOCKED for full-score multi-ticker performance claims.** Existing price-only pilot remains exploratory and separate.
