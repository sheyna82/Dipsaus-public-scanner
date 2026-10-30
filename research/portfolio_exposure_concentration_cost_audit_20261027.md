# DIPSAUS — portfolio exposure, concentration and cost diagnostic (2026-10-27)

Research-only follow-up to `research/six_position_portfolio_audit_20261027.md`. Derived **from the six previously generated trade-ledger CSVs**, not from a new independent backtest. Underlying prices are unverified. All results are exploratory; **NO-GO** for live strategy promotion.

The six position ledgers use fixed 3,500 notional per trade and initial 21,000 account units. Daily approximate exposure counts each entry date up to but excluding exit date, on weekday grid 2025-01-02 to 2026-10-27. This is a **slot-occupancy proxy**, not an independently recomputed daily cash book or exposure-weighted benchmark.

| Holding sessions | Sector max | Trades | Mean six-slot occupancy | Zero-position weekdays | Most profitable symbol | Its net trade P&L | Total net trade P&L | Total P&L with *additional* 50bp cost |
|---|---|---:|---:|---:|---|---:|---:|---:|
| 5 | 1 | 169 | 30.9% | 23.0% | NEM | 1,461.90 | 2,046.07 | -911.43 |
| 5 | 6 | 186 | 34.0% | 22.6% | FCX | 1,659.04 | 2,149.36 | -1,105.64 |
| 10 | 1 | 101 | 36.8% | 17.7% | FCX | 1,811.46 | 4,103.79 | 2,336.29 |
| 10 | 6 | 111 | 40.4% | 17.5% | FCX | 1,706.17 | 2,913.14 | 970.64 |
| 15 | 1 | 73 | 40.0% | 11.6% | NEM | 1,770.90 | 2,854.95 | 1,577.45 |
| 15 | 6 | 86 | 47.2% | 12.0% | FCX | 2,185.98 | 4,387.28 | 2,882.28 |

P&L values are in **currency-neutral simulation units**, not EUR-denominated verified returns. Extra-cost sensitivity deducts an additional 0.5% of fixed 3,500 entry notional per completed trade, on top of the original 0.5% round-trip assumption. It is an arithmetic sensitivity, **not a resimulated portfolio** (cash availability, ranking, and missed entries could change).

**Important:** In all six variants the best-contributing ticker accounts for a large fraction of gross positive symbol contributions. The five-session variants' positive net trade P&L flips negative when the cost assumption doubles from 0.5% to 1.0%. This does not prove 1% costs are typical; it highlights turnover sensitivity.

Next gates: independent daily portfolio engine, mark-to-market cash and FX, dividends/corporate actions, timestamp-safe signal availability, capacity/liquidity, matched exposure benchmark, chronological purged out-of-sample tests, expanded Europe/US DEGIRO universe, and stress testing market drawdowns. No stop orders, no automatic trades, no main merge.
