# EU next-session open, whole-share joint capital study — 2026-11-09

**RESEARCH ONLY — NOT AN APPROVED SIGNAL.**

Independent recomputation from GitHub Actions stock artifact 13667326575 and benchmark artifact 13667661996; only sessions completed through 2026-11-06. Two consecutive positive benchmark-relative closes trigger an event. Entry at **next session open**, whole shares; exit at close **5 or 10 completed sessions after entry**. €50,000 initial cash, €3,500 tranche maximum, 6 concurrent positions, no same-symbol overlap, no same-day reuse of proceeds. Candidate priority is deterministic chronological/alphabetical, not predictive. **RHM.DE mapped to DAX price index** (not STOXX Europe 600). Illustrative fee €4.90 each side and roundtrip 0.15% slippage, unverified against DEGIRO tariff.

| Horizon after entry | Trades | Gross P&L | P&L after illustrative costs |
|---|---:|---:|---:|
| 5 sessions | 52 | see JSON | **-€4,959.22** |
| 10 sessions | 31 | see JSON | **-€588.15** |

Net by stock, 5 sessions: ASML -€611.42; Infineon -€2,160.01; Nokia -€1,876.85; Rheinmetall -€310.94.
Net by stock, 10 sessions: ASML +€801.54; Infineon +€463.65; Nokia -€1,610.21; Rheinmetall -€243.15.

This is a **revised methodology**, not an apples-to-apples comparison with prior signal-close simulation: different entry, full post-entry holding horizon, corrected RHM national benchmark and integer share sizing. No claim of net edge; severe small-sample, overlapping-signal, baseline, index identity and OMXH25 close discrepancies. Corporate action/adjustment treatment and real execution costs still require verification. Neither horizon qualifies for deployment.

Source local reproducibility script: `eu_next_open_study.py`; output `DIPSAUS_EU_next_open_capital_study_20261109.json`. Both are conversation artifacts, not part of the repo. Repo ledger module hold-period bug fixed commit c7d7974; corresponding offline tests updated commit 8de27cbc. CI for latest commits must be independently checked.
