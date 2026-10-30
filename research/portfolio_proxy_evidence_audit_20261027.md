# Portfolio-level evidence audit — 2026-10-27

Source: existing **unverified** GitHub Actions artifact 12739376023 from run 40515277880, file `portfolio-proxy.json`, commit 8a5949b. This is an audit of **already computed** portfolio simulations, not a newly validated backtest. No strategy promotion.

## Whole-period comparison

Initial capital €21,000, maximum **three** simultaneous positions (not requested six). The portfolio proxy reports SPY buy/hold +65.4349% net (no dividends). Fifteen-session, no-warning exits:

| Maximum exposure | Final equity | Total return | Maximum mark-to-market drawdown |
|---|---:|---:|---:|
| 50% | €28,736.26 | +36.8393% | -21.4911% |
| 75% | €25,491.07 | +21.3861% | -29.5006% |
| 100% | €34,265.11 | +63.1672% | -26.8085% |

No comparison beats SPY in this specific whole-period set; exposure and trade timing differ, so this is not risk-adjusted attribution.

## Chronological holdout (pre-existing, exploratory)

The artifact includes **eight** chronological holdout combinations, all with 50% maximum exposure and max three positions. Holdout SPY buy/hold +39.6848%. Values below are portfolio return / maximum drawdown:

| Horizon | Warning exits | Max one per sector | Return | Max drawdown |
|---|---|---|---:|---:|
| 10 | No | No | +24.0249% | -6.3802% |
| 10 | No | Yes | +6.3414% | -7.3421% |
| 10 | Yes | No | +19.8369% | -7.8311% |
| 10 | Yes | Yes | +31.1916% | -5.2966% |
| 15 | No | No | +4.3319% | -11.2208% |
| 15 | No | Yes | +13.1714% | -6.2442% |
| 15 | Yes | No | +36.1297% | -5.4066% |
| 15 | Yes | Yes | +29.9237% | -5.0304% |

Every variant underperforms SPY on absolute return. The 15-day warning-exit no-sector-cap variant has +36.13%, but only retrospective exploratory holdout and is not a validated improvement. The 15-day warning-exit sector-cap variant has +29.92%, and stress with per-side slippage 0/5/10/20/40 bps reduces return to +29.92/+27.88/+25.83/+21.75/+13.62%, respectively.

## Methodological blockers

- Price artifact expressly unverified; adjustment, survivorship and licensing unverified.
- Historical holdout is retrospective and **not** untouched prospective validation; many variants evaluated, risking selection bias.
- Maximum three positions, not DIPSAUS requested maximum six; fixed €21k initial capital.
- Benchmark lacks dividends and is not risk-adjusted; portfolio dividends and FX not modeled.
- Artifact explicitly sets `risk_adjusted_benchmark_tested=false`, `trade_ready=false`; fractional shares assumed.
- Warning exits are **research simulations**, not authorization to place stoploss or stop-limit orders.
- Do not compare selected high-return variants without accounting for all searched combinations.

**Decision: NO-GO** for live promotion. Next: validate corporate actions/source, simulate six-slot €3,500 allocations, risk-adjusted and time-matched SPY comparison, test untouched periods and EU symbols, report actual net portfolio performance.
