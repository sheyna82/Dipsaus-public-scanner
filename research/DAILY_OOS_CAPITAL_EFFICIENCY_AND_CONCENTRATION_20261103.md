# Daily OOS capital-efficiency and single-trade concentration — artifact 13007728223

Inspected source: `candidate_feature_oos.json` inside GitHub Actions artifact 13007728223 (run 41121367948). Research-only 10-session portfolio simulation; 50 bps cost, €3,500 tranche, €21,000 initial capital, six-position maximum. Figures are model PnL, not realized brokerage outcomes.

## Capital occupancy, reproduced from archived accepted trades
Each accepted trade consumes one €3,500 tranche for `exit_day-entry_day+1` **calendar days**, not trading days. The inclusive exit-day convention exactly reproduces the archived `occupied_tranche_calendar_days` for all four arms. The denominator is **€ × calendar-days** and is not average deployed capital, annualized ROI or risk-adjusted return.

| Pattern | Arm | Accepted trades | PnL € | Occupied tranche calendar-days | Capital €-days | PnL € per €1,000 capital-day | Maximum concurrent positions |
|---|---|---:|---:|---:|---:|---:|---:|
| Recovery | baseline | 238 | 7141.74 | 3331 | 11658500 | 0.612578 | 6 |
| Recovery | filtered | 78 | 720.58 | 1101 | 3853500 | 0.186994 | 5 |
| Breakout | baseline | 183 | 3376.87 | 2573 | 9005500 | 0.374979 | 6 |
| Breakout | filtered | 15 | 955.40 | 216 | 756000 | 1.263757 | 3 |

Recovery baseline/filtered efficiency ratio = 3.276; breakout filtered/baseline ratio = 3.370. These are **descriptive ratios** of distinct selected portfolios, NOT causal improvements from filters.

## Single-trade sensitivity (recomputed from each accepted trade's net_return_pct × €3,500)
| Pattern | Arm | Winning trades | Largest single gain € | Largest single loss € | PnL after removing largest winning trade € |
|---|---|---:|---:|---:|---:|
| Recovery | baseline | 125/238 | 1420.32 | -655.79 | 5721.42 |
| Recovery | filtered | 42/78 | 888.78 | -575.68 | -168.20 |
| Breakout | baseline | 88/183 | 1687.62 | -1132.55 | 1689.25 |
| Breakout | filtered | 8/15 | 845.23 | -292.60 | 110.17 |

The filtered recovery total is entirely dependent on its single best trade in this sensitivity. Filtered breakout has only 15 accepted trades; its efficiency ranking is not statistically validated.

## Research implications
- The recovery filter is not supported for promotion by observed capital efficiency or single-trade robustness.
- The breakout filter is a hypothesis for further testing, **not** validated alpha: sparse events, no matched capital opportunity cost, no confidence intervals, no independent fills or drawdown.
- Baseline `priority_mode=symbol_asc` is an alphabetical capacity-selection policy, **not** a professional ranking rule. Re-run both arms with a common candidate event pool and multiple ex-ante priority policies, paired capacity constraints and deterministic tie-breaking.
- Need daily marked-to-market portfolio equity, FX, corporate-action, earnings/spread and execution audits before live decisions.
- No changes to live scanner, notification gate, orders, or main branch.
