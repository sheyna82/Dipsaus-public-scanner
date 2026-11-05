# Free historical OHLC source decision (research, 2026-10-21)

## Decision: no unverified provider integrated yet

We need real, point-in-time daily OHLCV, delisted securities, splits, volume,
market benchmarks, and a documented lawful use policy. A downloadable CSV alone
does not meet these requirements.

### Sources assessed

- **Stooq**: broad free historical OHLC downloads, but automated CSV retrieval
  may be blocked by challenge/quota, personal-use/redistribution restrictions
  apply, and corporate-action and point-in-time semantics are not sufficiently
  documented for a validated full-universe backtest.
  https://stooq.com/
- **OHLC.Stock (ohlc.io)**: advertises free 5-year EOD for only AAPL, NVDA,
  JNJ, PEP, MSFT, SPY and QQQ; broader symbols, European stocks, and longer
  history are paid. This cannot validate a diverse DIPSAUS universe for free.
  https://ohlc.io/data/historical-stock-prices
- **Roic AI**: advertises free stock-price API with only two years of historical
  access. Insufficient for robust regime-spanning validation.
  https://www.roic.ai/api/docs/stock-prices/historical
- **Nasdaq historical exchange products**: commercial licensing and fees;
  not appropriate for the strict zero-cost requirement.
  https://www.nasdaqtrader.com/content/AdministrationSupport/Policy/USEquityTickHistoryPolicy.pdf

### Safe next steps

1. Pilot with user-supplied, locally stored OHLCV data whose permitted use and
   corporate-action policy are independently checked. Do NOT commit raw bars,
   tokens, user holdings or private data to this public repository.
2. Build a local **OHLCV-to-features** adapter with causal rolling windows.
   Exclude the signal bar's close from any signal generated *before* that close.
3. Enforce real release timestamps for events/earnings; do not substitute a
   fabricated publication timestamp or infer one from a price date.
4. Preserve delisted constituents and time-specific universe membership;
   otherwise label any pilot **survivors-only exploratory**, not validated.
5. Run fixed-parameter chronological holdout against simple baseline and
   report all coverage/exclusions, including fees, slippage and limit fills.
6. Keep all outputs research-only until a genuine out-of-sample advantage is
   independently demonstrated.

This is a source review, NOT a successful live API connection, downloaded
historical dataset, or proven prediction model.
