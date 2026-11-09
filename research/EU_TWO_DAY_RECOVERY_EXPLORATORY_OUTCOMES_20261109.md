# EU recovery two-positive-session exploratory outcomes — 2026-11-09

**HISTORICAL EXPLORATION ONLY; NO TRADING SIGNAL OR VALIDATED EDGE.**

Inputs: stock artifact 13663604213 and benchmark artifact 13666078191; completed common sessions through 2026-11-06. Candidate event = two consecutive daily stock returns outperform their national price benchmark (positive percentage-point differences). Correctly includes the latest of the two sessions (fix commit 312f725d). Signal evaluated using that session's close. Forward outcomes are **close-to-close**, 5 and 10 common sessions later; not executable fills.

| Stock | All events | 5-session evaluated | Mean gross stock return 5d | Positive 5d | 10-session evaluated | Mean gross stock return 10d | Positive 10d |
|---|---:|---:|---:|---:|---:|---:|---:|
| ASML.AS | 33 | 33 | -0.41% | 54.5% | 30 | +1.76% | 50.0% |
| IFX.DE | 33 | 32 | -2.63% | 34.4% | 30 | -2.77% | 36.7% |
| NOKIA.HE | 22 | 22 | -5.48% | 13.6% | 19 | -1.00% | 42.1% |
| RHM.DE | 30 | 30 | -0.20% | 43.3% | 29 | -2.33% | 41.4% |

All figures rounded from observed historical daily Yahoo series. **Critical limits:** events overlap heavily and are not independent trades; same symbol can trigger on adjacent days, and exits can overlap. This is in-sample exploratory screening, not a strategy backtest, not portfolio-capital constrained, no spread, commissions, FX, slippage, dividends, taxes, event risk, liquidity or survivorship adjustments. Benchmarks still have unresolved identity crosswalk and OMXH25 close discrepancy. No ex-ante validated EU threshold or broker instrument gate. Consequently, no evidence of positive net expected return, and no stock passes a buy gate.

**Next:** implement nonoverlapping, capital-constrained event ledger, matched baseline and forward-only out-of-sample design before any conclusions.
