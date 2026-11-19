# European recovery structure — multi-horizon historical diagnostic (2026-11-09)

**RESEARCH ONLY — NOT A BUY SIGNAL.** Uses completed daily bars through **2026-11-06**, excludes partial 2026-11-09 bars.

Input GitHub Actions artifacts: stock 13663604213, benchmark 13666078191. Alignment: UTC dates of daily series; last common session and 1, 3, 5, 10, 20 preceding common sessions. Relative strength (pp) = stock simple price return (%) minus national index simple price return (%).

| Stock | 1-session RS (pp) | 3-session RS | 5-session RS | 10-session RS | Volume / prior 20 sessions | ATR14 / close |
|---|---:|---:|---:|---:|---:|---:|
| ASML.AS | +3.4558 | -7.2134 | -7.9206 | -7.8043 | 1.7330 | 4.9047% |
| IFX.DE | +1.4926 | -12.5101 | -9.5118 | -8.5257 | 1.6325 | 6.3350% |
| NOKIA.HE | +2.5064 | -9.2279 | -10.3600 | -5.9842 | 1.1532 | 6.2467% |
| RHM.DE | -1.5054 | -18.9471 | -21.6833 | -22.7817 | 2.3249 | 5.6382% |

**Interpretation:** ASML, Infineon and Nokia show a *one-session* relative bounce on November 6, but remain relatively weak across 3–10 sessions. Rheinmetall did not even outperform its national index on the last completed day. Volume and volatility are elevated for several names; these do not prove a reversal. **None qualifies as an approved recovery entry.**

Source/eligibility gates remain unresolved: provider-index identity not fully verified; OMXH25 official-vendor close discrepancy; DEGIRO exact instrument eligibility unverified; no EU-calibrated out-of-sample thresholds; execution cost and event review outstanding. No changes to frozen U.S. protocol, main, live scanner or orders.

Machine-readable reproducibility output: `DIPSAUS_EU_multihorizon_recovery_diagnostic_20261109.json` (generated separately from immutable downloaded artifacts).
