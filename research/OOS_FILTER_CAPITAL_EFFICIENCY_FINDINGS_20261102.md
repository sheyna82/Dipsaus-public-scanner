# OOS filter comparison: realized capital efficiency and quarter concentration (2026-11-02)

Source: GitHub Actions run 41121367948, artifact 13007728223, files `candidate_feature_oos.json` and `candidate_feature_portfolio_quarters.json`. Independently re-read and compared. HISTORICAL RESEARCH only; source prices not independently verified, no daily mark-to-market equity or prospective validation.

| Pattern | Arm | Accepted | Realized P&L (€ proxy) | Return on €21k (%) | P&L per €1000 capital-calendar-day unit | P&L without best quarter (€ approx) |
|---|---|---:|---:|---:|---:|---:|
| breakout_prior20 | baseline | 183 | 3376.87 | 16.0803 | 0.374979 | -1152.14 |
| breakout_prior20 | filtered | 15 | 955.40 | 4.5495 | 1.263757 | 115.49 |
| recovery_from_prior20_low_3to15pct | baseline | 238 | 7141.74 | 34.0083 | 0.612578 | 2000.18 |
| recovery_from_prior20_low_3to15pct | filtered | 78 | 720.58 | 3.4313 | 0.186994 | -587.63 |

**Interpretation:** The combined three-feature filter does not improve total portfolio return in either pattern. For recovery, it also reduces capital-calendar-day efficiency and loses money after excluding the strongest quarter. For breakout, the filtered arm has higher realized capital occupancy efficiency, but only 15 accepted trades and substantial sampling uncertainty; do not promote to live decision gate. Different accepted portfolios mean differences in raw cumulative P&L are not a matched-trade causal estimate. The returns are proxy realized P&L / €21k initial capital, not compounded equity or annualized performance.

**Existing components to reuse:** `research/candidate_feature_oos.py`, `research/candidate_portfolio_quarter_diagnostics.py`, `research/candidate_portfolio_capacity.py`. No new calculator or filter implementation warranted from these results.

**Next test:** Use the existing historical per-event feature and candidate audit to test each filter separately within the common held-out calendar, retaining the same capacity policy, execution costs and entry timestamp. Report trade count, total P&L, capital efficiency, quarter concentration, and uncertainty; do not select a winning configuration on the same held-out period without a new prospective validation period.
