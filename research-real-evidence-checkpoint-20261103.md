# DIPSAUS — real-evidence checkpoint, 2026-11-03

## Verified inputs
- AMD manual Finnhub capture: run [41712197672](https://github.com/sheyna82/Dipsaus-public-scanner/actions/runs/41712197672), artifact 13268535597, preserved JSON `research-evidence/amd-20261103-source-observation.json`.
- CSGP manual Finnhub capture: run [41716597106](https://github.com/sheyna82/Dipsaus-public-scanner/actions/runs/41716597106), artifact 13269669790, preserved JSON `research-evidence/csgp-20261103-source-observation.json`.
- [CI run 41717942995](https://github.com/sheyna82/Dipsaus-public-scanner/actions/runs/41717942995): 262/262 isolated tests passed, including source integrity, one-day coverage and provider-claimed timestamp lag.
- Both provider timestamps precede their captures by approximately 18.43 s (AMD) and 19.60 s (CSGP); these are **provider assertions**, not independent clock proofs.

## CSGP issue #63 reconciliation
The 2026-11-02 scanner issue records an **unverified** provider quote of $31.065 and BREAKOUT-HOLD-RETEST phase. The 2026-11-03 Finnhub capture reports $31.28, an arithmetic difference of $0.215 (~0.692%). These are different provenance channels and times; the difference is **not** an executable return, a verified daily close, a recovery success, or a buy signal. No independent OHLCV, bid/ask spread, transaction cost, earnings/news assessment, or portfolio-fit decision has been completed.

## Evidence state
- Real archived source observations: **2**.
- Distinct symbols: **2**.
- Distinct UTC days: **1**.
- Pre-registered real trade candidates: **0 verified in this evidence set**. This is not a claim that no candidates exist anywhere in the project.
- Independently authenticated market observations: **0 verified in this evidence set**.
- Prospective outcomes: **0 verified in this evidence set**.
- Trading edge or trade readiness: **not established**.

## Next evidence-producing action
On a **subsequent US trading session**, manually run the existing Finnhub observation workflow for a previously observed symbol (prefer CSGP for issue #63 continuity). Download and preserve its original artifact immediately; independently confirm its date, timestamp, and price before treating it as market evidence. Do not activate scheduled collection or modify main. Continue manual observations across distinct days and independently sourced daily OHLCV; pre-register candidates **before** future outcomes, never backdate registration. The technical 20-observation / 5-day smoke threshold is not a statistical profitability criterion.

No live scanner, private repo, ntfy, cron, credentials or trading orders changed.
