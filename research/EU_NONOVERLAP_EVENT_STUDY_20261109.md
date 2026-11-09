# EU nonoverlapping historical event study — 2026-11-09

**RESEARCH ONLY. NOT TRADE READY. NOT A CAPITAL-CONSTRAINED PORTFOLIO BACKTEST.**

Recomputed independently from completed daily Yahoo history in GitHub Actions artifacts stock **13667326575** and benchmark **13667661996**. Data cutoff 2026-11-06; exclude partial 2026-11-09. Two consecutive positive one-day benchmark-relative returns define an event at the second day's close. A position is hypothetically entered at that close (optimistic/unexecutable assumption) and exited at the close 5 or 10 common sessions later. No new position in the same symbol until the prior exit session has passed. Results below are mean gross stock returns and counts.

| Stock | 5d nonoverlap count | Mean 5d gross | 10d nonoverlap count | Mean 10d gross | All-start-day 10d mean |
|---|---:|---:|---:|---:|---:|
| ASML.AS | 12 | +0.094% | 7 | +2.958% | +0.635% |
| IFX.DE | 15 | -2.843% | 8 | +0.652% | -2.069% |
| NOKIA.HE | 11 | -4.326% | 8 | -4.520% | -3.566% |
| RHM.DE | 14 | -0.654% | 9 | -1.865% | -1.250% |

Caveats: baseline uses every eligible start day and is overlapping; this is a descriptive comparator, **not a matched or independent control**. Event samples are small, in-sample and vulnerable to regime selection. No broker costs, slippage, FX, bid/ask spread, dividends, portfolio-level competing signals, max-six positions, €50k cash ledger, financing, or statistical uncertainty assessed. Index identity not independently approved; Helsinki index reference close conflict unresolved. Data provider history may be adjusted; source methodology requires further verification. No positive net expected return or trading readiness established.

Reproducibility: the independently computed JSON file `DIPSAUS_EU_nonoverlap_exploratory_20261109.json` is available as a conversation artifact, with counts and selected dates. Next: prospective OOS evaluation, fee sensitivity, capital occupancy, synchronized cross-symbol ledger, uncertainty intervals and controls.
