# DIPSAUS — six-position portfolio exploratory audit (2026-10-27)

**Research only, NO-GO for live promotion.** Source GitHub Actions artifact 12739376023, run 40515277880, `dipsaus-diversified-sector-prices-unverified` (18 US stocks and SPY/IWM). Daily prices unverified; survivorship and split/dividend adjustments not independently audited.

**Fixed model:** 2025-01-02 through 2026-10-27; starting capital 21,000 **currency-neutral units** (USD-priced stocks; do NOT interpret as a EUR-converted result); six slots, fixed 3,500 per entry, fractional shares, cash-only, 25bps each side, no stop-loss, trailing 20-session close maximum, signal >=10% dip at previous session close, entry at next open, exit at open after 5/10/15 sessions. Strongest drawdown first when several candidates compete (arbitrary, unvalidated ranking); compare at most one symbol per sector versus no sector restriction. Daily close mark-to-market; final result has no open positions because new entries are halted near the data boundary. No dividends, FX, financing, bid/ask or actual DEGIRO fees. This is a **retrospective, non-pre-registered** comparison; don't treat as untouched holdout.

| Horizon | Sector cap | Total return | Max drawdown | Completed trades |
|---|---|---:|---:|---:|
| 5 | 1 | +9.74% | -14.93% | 169 |
| 5 | none | +10.24% | -14.71% | 186 |
| 10 | 1 | +19.54% | -14.26% | 101 |
| 10 | none | +13.87% | -13.73% | 111 |
| 15 | 1 | +13.59% | -15.55% | 73 |
| 15 | none | +20.89% | -15.25% | 86 |

SPY same date buy at first open and mark at last close, 50bps round trip: **+29.51%**, dividends excluded. No tested DIPSAUS portfolio beats this absolute-return benchmark. Differences in market exposure mean this is not yet risk-matched.

**Known caveats:** portfolio ignores pending orders, currency conversion, dividends, trading halts, volume constraints, borrow constraints, and corporate actions; candidate ranking is an arbitrary implementation decision; signal conditions re-evaluated for all currently unheld symbols each day; cash cannot fund a full 3,500 slot if losses leave insufficient cash. The close-based signal is observed before the following open. No automatic orders or merge to main.

**Next tests:** risk-matched SPY benchmark (same invested fraction), cross-sectional concentration and sector contributions, liquidity and split audit, transaction cost stress, distinct future untouched windows, European equities, and stable ranking rules.
