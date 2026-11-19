# European joint-capital exploratory ledger — 2026-11-09

**RESEARCH ONLY — NO APPROVED TRADES OR LIVE CHANGES.**

Independent local recomputation from GitHub Actions artifacts stock 13667326575 and benchmark 13667661996, using completed bars through 2026-11-06. Two consecutive positive daily benchmark-relative returns trigger a candidate. Hypothetical €3,500 entry at *signal close* and exit at close after 5 or 10 common sessions; these entry prices are **not executable as assumed**. Starting cash €50,000; max 6 simultaneous positions; same-symbol overlapping positions excluded; alphabetic ordering of same-day candidates, not a validated priority. A hypothetical €4.90 per side + 0.15% of allocation round-trip spread/slippage is charged (€15.05 per trade). Broker fee is **illustrative, not DEGIRO-verified**. No FX, dividend, taxes, connectivity fees, corporate actions or financing.

| Horizon | Executed hypothetical trades | Gross P&L | Illustrative costs | P&L after illustrative costs | Rejected candidate events |
|---|---:|---:|---:|---:|---:|
| 5 common sessions | 50 | -€3,381.85 | €752.50 | **-€4,134.35** | 67 |
| 10 common sessions | 31 | -€374.50 | €466.55 | **-€841.05** | 77 |

Same-day reuse true/false produced identical counts and totals under this implementation, because exits and entries of the same symbol on one day were conservatively disallowed. With only four instruments and no pyramiding, the six-position cap cannot bind; this **does not test real six-position competition**. Unused cash is substantial. Results are in-sample, small, nonrandom, unadjusted for splits and possible vendor corporate actions. The index identity gate is unresolved and OMXH25 vendor reference discrepancy persists. Critically, this is **not** a validated predictive strategy or executable backtest.

Calculation script and complete trade ledger in conversation artifacts `eu_portfolio_study.py` and `DIPSAUS_EU_capital_ledger_exploratory_20261109.json`. No claim of positive edge; next priority: test broker fees from official source, entry next tradable session, exact share counts, portfolio occupancy, matched comparator, prospective OOS.
