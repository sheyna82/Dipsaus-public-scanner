# EU recovery evidence gate — 9 November 2026

Status: **RESEARCH ONLY — BLOCKED**. No changes to main, live scanner, execution or protocol thresholds.

## Independent DEGIRO tariff sources

- Standard schedule https://www.degiro.nl/data/pdf/Tarievenoverzicht.pdf (effective 2025-10-01): Amsterdam €2 commission; Xetra and Nasdaq Helsinki €3.90 commission. Add €1 handling per side under applicable tariff.
- Custody schedule https://www.degiro.nl/data/pdf/Tarievenoverzicht_CUSTODY.pdf (effective 2026-01-01) corroborates these commission bands.
- Official page https://www.degiro.nl/tarieven explains connectivity: 0.25% of portfolio value, capped at €2.50 **per exchange per calendar year**, exempt Amsterdam/Brussels. Do not apply as per-trade fee.

For a €3,500 tranche: ASML.AS Amsterdam fixed round trip €6; IFX.DE and RHM.DE Xetra and NOKIA.HE Helsinki €9.80, before spread, slippage and possible additional charges. Spread round-trip scenarios of 0.1/0.3/0.5% add €3.50/€10.50/€17.50. Do not apply FX charges unless actual execution currency differs from account currency.

## Data and indicators

Source: GitHub Actions run 42598453139 artifact 13663604213. Captured 2026-11-09 10:07 UTC, while European markets were open. Exclude the incomplete 2026-11-09 daily bar from daily-close research. Latest complete session 2026-11-06. Stock-only 20-day returns (not relative strength): ASML -19.855%; IFX -22.265%; NOKIA -25.005%; RHM -13.460%. Volume ratios approximately 1.733/1.633/1.153/2.325. ATR14% approximately 4.905/6.335/6.247/5.638.

## Hard gates

1. **Benchmark missing**: select, justify and independently capture benchmark daily closes, align by local trading date; stock-only return must never be labeled relative strength. Europe-specific threshold calibration is unapproved; do not reuse frozen AMD/SPY thresholds automatically.
2. **DEGIRO eligibility**: exchange support does not prove exact ticker/ISIN is available in the user's DEGIRO account. `EXCHANGE_SUPPORTED_INSTRUMENT_UNVERIFIED` until checked.
3. **Signal completeness**: no current-session daily close until session ends; no full intraday OHLCV confirmation from this daily artifact.
4. **Economics**: connectivity per exchange/year, scenario spreads and slippage, existing positions, capital overlap and event risk must be included before candidate approval.

Conclusion: no approved buy signal, no automated orders.
