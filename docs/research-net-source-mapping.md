# EU/US source-to-net evidence mapping audit (research only)

Compared against `us_execution_gate.py`, `dipsaus_eur_upside.py`,
`europe_quote_execution_audit.py`, and `research_net_bridge.py`.
These are **different evidence contracts**. Do not copy provider prices into
broker fields or promote a gross research estimate into a net decision.

| Canonical net bridge field | US source | EU source | Integration rule |
| --- | --- | --- | --- |
| broker_ask, broker_bid | us_execution_gate: ask_usd, bid_usd only if independently broker-verified | europe_quote_execution_audit: provider_ask/provider_bid **not** broker quotes | Never auto-map provider quote; require DEGIRO evidence |
| invalidation, target | us_execution_gate: invalidation_usd, realistic_target_usd; require independently verified levels | No validated structural levels in quote audit | Explicit verified technical evidence only |
| fx_eur_per_unit | us_execution_gate: eur_per_usd with fx_utc | quote audit: currency only | Require independently verified conversion or explicit EUR=1 |
| buy_fee_eur, sell_fee_eur | Not modeled by us_execution_gate | Not modeled by quote audit | Require instrument/route-specific verified broker fees |
| fx_buy_fee_rate, fx_sell_fee_rate | Not modeled by us_execution_gate | Not modeled by quote audit | Explicit verified rates, including zero for confirmed no conversion |
| buy_slippage_per_share, sell_slippage_per_share | Not modeled by us_execution_gate | Not modeled by quote audit | Explicit scenario assumptions, no silent default zero |
| quote_freshness_verified | US quote_utc <=300s check, plus independent broker verification | EU provider_freshness_pass is **not** broker freshness | Broker timestamp and freshness must be independently established |
| broker_quote_verified | US field exists but evidence provenance not supplied by bridge | EU audit always False | Never set True from provider data |
| levels_verified | US separate technical flags | EU quote audit has no structural level verification | Do not conflate target with first resistance |
| fees_verified | Absent | Absent | Fail closed |
| fx_verified | US field exists | Absent | Independently verify |
| risk cap / news / earnings / liquidity / portfolio fit | US execution gate has partial flags, risk cap optional | EU quote audit does not cover these | Net bridge **does not** grant trade readiness or replace other gates |

The bridge currently calculates a non-executable net scenario. It does not
validate timestamps, exchange route, liquidity, corporate events, news,
first meaningful resistance, max risk or portfolio fit. A verified bridge
result means only that the **supplied** input flags were True; it does not
independently attest their provenance. The next stage must design a
separate attestation and freshness envelope before any scanner integration.

`trade_ready` and `order_placement_enabled` remain False in every case.
Do not modify production or draft PR #65.
