# Safe, free software candidates for DIPSAUS (2026-10-23)

Status: RESEARCH CANDIDATES ONLY. No installation, live alerts, model promotion, or trading actions authorized by this document.

## Immediate, low-risk additions (prefer standard library first)
1. **Data quality gate**: validate unique sorted trading dates, OHLC invariants, positive finite prices/volume, timezone consistency, missingness, adjusted/raw provenance, split discontinuities. Fail closed and report missingness. Pandera (MIT) is optional after dependency/security review; Python assertions/schema checks may suffice.
2. **Prediction and alert journal**: append reproducible as-of timestamp, source hashes, symbol, model version, eligibility, score, uncertainty, alert decision and later outcome separately. No personal holdings or secrets in this public repository.
3. **Research validation**: preserve frozen ATR protocol, train-only fitting, date-clustered uncertainty, embargo, multiple-testing registry, negative results, costs, delisting and survivorship checks. No claim of predictive performance before untouched holdout.
4. **Risk and calibration reports**: existing Brier/log-loss first; evaluate whether QuantStats (Apache-2.0) adds enough value to justify its dependencies.

## Separate offline experiments
- **EdgarTools** (MIT): SEC filing metadata and as-of publication timestamps; comply with SEC fair-access limits and identification; avoid downloading or publishing unlicensed bulk datasets. American issuers only; filings do not solve daily price holdout.
- **River** (BSD-3-Clause): sequential drift alarms; require prospective evaluation and false-alarm budget before operational alerts.
- **ruptures** (BSD-2-Clause): retrospective changepoint analysis only; do not treat full-series breakpoints as live forecasts.
- **Sector relative strength, three-phase recovery, selling-exhaustion, cross-asset stress and meta-labeling**: test incremental value versus simple frozen baseline using independent data. Data coverage and timing must be verified.
- **Great Expectations** (Apache-2.0): reserve; likely unnecessary for current small pipeline.

## Supply-chain / deployment gates
- Check upstream repository, current release, license, maintenance, advisories, Python compatibility and transitive dependencies before installation; pin hashes/versions; no untrusted Actions or installation scripts.
- No paid services, API keys in public repository, private holdings, automatic orders, stoploss execution, or changes to production scanner.
- Keep all work on research branch and do not merge PR #62 without explicit approval.
- Research priorities: (1) data validation/journal (2) truly independent point-in-time data (3) holdout scoring (4) experimental model comparisons.
