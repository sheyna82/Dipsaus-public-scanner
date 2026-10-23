# DIPSAUS — external research software adoption gate (2026-10-23)

Research-only inventory. No external packages have been installed, vendored, or enabled. License declarations do not certify dependency security or historical-data rights.

| Candidate | Upstream | Declared license | Targeted reuse | Decision |
| --- | --- | --- | --- | --- |
| scikit-learn | https://github.com/scikit-learn/scikit-learn | BSD-3-Clause | calibration, Brier score, time-aware cross-validation reference | Evaluate isolated, pinned version first |
| statsmodels | https://github.com/statsmodels/statsmodels | BSD-3-Clause | confidence intervals, robust inference with dependent observations | Evaluate isolated, pinned version first |
| pandas | https://github.com/pandas-dev/pandas | BSD-3-Clause | date-index validation and OHLCV auditing | Optional offline only |
| Microsoft Qlib | https://github.com/microsoft/qlib | MIT | point-in-time data architecture and experiment methodology | Study architecture; defer installation |
| QuantStats | https://github.com/ranaroussi/quantstats | Apache-2.0 | drawdown and risk reporting on simulated realized returns | Defer until executable returns exist |

## Gate before any dependency installation

1. Confirm exact upstream release tag, release date, supported Python and actual LICENSE/NOTICE, including transitive dependencies.
2. Pin exact package versions and hashes in a research-only lock file; never install from an unpinned Git branch.
3. Scan dependency tree and pinned versions for published vulnerabilities; record scanner, timestamp, and advisory results. No unverified safety claims.
4. Keep workflows read-only with least privileges, no private credentials, no live orders, no data download or upload, and no package installation from arbitrary paths.
5. Run synthetic and real-data provenance tests offline; benchmark against the existing zero-dependency implementation.
6. Adopt only if measurable benefits outweigh maintenance and supply-chain costs; retain attribution when copying code.
7. Do not infer a market prediction edge from a library's reputation, test pass, or synthetic examples.

## Immediate high-value comparisons

- scikit-learn: compare Brier score/log loss to DIPSAUS calculations; check probability calibration with strictly chronological train/validation/test splits. TimeSeriesSplit alone does not solve future-label availability, corporate-action leakage, or overlapping financial outcomes.
- statsmodels: investigate block-bootstrap or autocorrelation-robust uncertainty estimates for paired ATR-minus-baseline loss differences. IID confidence intervals are inadequate for overlapping forward-return labels.
- QuantStats: do not feed classification probabilities into trading-return analytics; require strategy decisions, fill assumptions, costs, and returns first.
- Qlib: distinguish historical price date from historical availability date. Standard time-series splits do not prove point-in-time validity.

Official references:
- https://github.com/scikit-learn/scikit-learn/blob/main/COPYING
- https://github.com/scikit-learn/scikit-learn/security/policy
- https://github.com/statsmodels/statsmodels/blob/main/LICENSE.txt
- https://github.com/microsoft/qlib/blob/main/pyproject.toml
- https://github.com/ranaroussi/quantstats/blob/main/pyproject.toml

Status: upstream documentation reviewed; full transitive-license audit, exact release pinning, vulnerability scan, installation and empirical performance comparison not yet performed.
