# DIPSAUS — independent audit of exploratory recovery confirmation results (2026-10-27)

**Status: exploratory only; not an out-of-sample backtest or trade recommendation.**

Input: locally calculated `dipsaus_recovery_confirmation_trades.csv`, derived from the eight-stock GitHub Actions artifact `dipsaus-notification-prices-unverified` (artifact 12738497651, run 40515277501, commit 8a5949b). Six symbols actually generated qualifying signals: EXE, FANG, FER.MC, MBG.DE, MC.PA, VIST. Original downloaded source marked **unverified**. The local derived CSV is **not committed** because its source provenance and redistribution status are not yet independently reviewed.

## Method and limitations

Signals: trailing 20-session high, at least 10% close drawdown; compare plain dip, one positive close, two positive closes, and close above five-session moving average. Next-session open entry; open exit after 3, 5, 10, or 15 sessions. Deduct 50 bps round-trip. No overlapping same-symbol trades *within a strategy/horizon*, but observations **across strategies and horizons overlap**. Short window (signal decisions 2026-08-26 through 2026-10-15); no complete market cycle, delisted-universe control, independently verified adjusted-price data, financing/FX, liquidity screening, sector-neutral weighting, or true holdout. **No edge established.**

## Ten-session horizon, all observed signals

| Signal | Trades | Symbols | Mean net return |
|---|---:|---:|---:|
| Dip only | 13 | 6 | -0.63% |
| One positive close | 9 | 6 | -1.75% |
| Two positive closes | 6 | 5 | -3.56% |
| Close above MA5 | 6 | 6 | +0.99% |

The apparent MA5 winner depends heavily on a single VIST trade (+7.80%). Excluding VIST leaves five trades averaging about **-0.37%**. Thus no reliable evidence of an advantage.

## Calendar-split diagnostic (NOT a true out-of-sample test)

Using decision date before vs on/after **2026-09-25**, for ten-session holding:
- Dip only: earlier **8 trades, -4.22%** mean; later **5 trades, +5.12%** mean.
- Above MA5: earlier **3 trades, +0.55%** mean; later **3 trades, +1.43%** mean.
- One positive close: earlier **6 trades, -3.24%** mean; later **3 trades, +1.24%** mean.
- Two positive closes: earlier **5 trades, -3.29%** mean; later **1 trade, -4.93%** mean.

The split is *post-hoc* and the source window is tiny; it illustrates regime sensitivity, not validation. Signal trades may be correlated by date and market shock.

## Decision gate

**NO-GO for strategy promotion**. Continue only after:
1. Source-license/provenance and adjustment audit; multiple years of US and European data including delisted stocks where possible.
2. Pre-register fixed signal parameters and 5/10/15-day horizons; hold out chronological periods and symbols, with purging/embargo near boundaries.
3. Report per-symbol and sector exposure, drawdown/MAE, tail losses, win rate, expectancy, turnover, costs and slippage stress, and matched-date baseline.
4. Validate results on truly unseen periods; no auto-orders, no merge to main without explicit authorization.
