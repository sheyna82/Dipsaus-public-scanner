# Multi-ticker out-of-sample protocol — preregistration (research only)

Status: PROTOCOL ONLY. No multi-ticker historical outcomes have been measured.

## Frozen before independent data are evaluated
- Universe: include all available US common-stock tickers with sufficient history, including delisted issuers when source provides them; report coverage and exclusions, do not select winners ex post.
- Dates: use chronological development/validation/test periods, separated by an embargo of at least 10 trading sessions (the fixed outcome horizon). Final untouched test is evaluated once.
- Signal: existing frozen offline recovery score, threshold >= 5 selected, < 5 skipped. No post-hoc optimization of thresholds using the test period.
- Earnings: do not substitute a fictional four-day earnings distance for production-grade testing; require authentic point-in-time earnings calendar or mark the test price-only and abstain from claims about the complete strategy.
- Entry and exit: next session open to tenth subsequent session close; 10 bps each side; nonoverlapping observations per ticker. Record unfilled/missing prices and corporate-action anomalies as exclusions, not zero returns.
- Downside: report fixed -3% terminal loss and any negative terminal return; these are NOT stoploss orders or intraperiod drawdown.
- Comparators: skipped cohort, broad benchmark and simple equal-weight candidate baseline, all with the same eligibility dates, costs and outcome horizon. Report sample counts and sector/year composition.
- Confidence: report counts, bootstrap uncertainty by ticker and time block (not individual overlapping events), stability by chronological period and market regime; no assertion of significance from a single small sample.
- Integrity: same-source adjusted OHLCV, verified corporate actions and compatible benchmark; inspect holidays, gaps, delisting coverage and survivorship bias. Record provider, timestamp, license, raw/adjusted policy, exclusions, and file hashes.
- Decision gate: no live changes, trade signals or calibrated probabilities without independent holdout, source verification, acceptable downside, and explicit approval.

Current limitations: prior Apple/SPY sample was inspected, chronologically unstable and is NOT untouched holdout. Local importer, cohort gate and data quality checks are preliminary engineering, not evidence of predictive performance. Candidate WIKI source ends in 2018 and requires verification of its free accessibility and rights.
