# DIPSAUS — professionele platformbenchmark (6 november 2026)

**Scope:** research-only. Vergelijking op basis van openbare projectdocumentatie; geen externe engines geïnstalleerd of getest. Geen claim dat DIPSAUS gelijkwaardig is aan institutionele platforms.

## Referenties

- [Microsoft Qlib: research workflow](https://github.com/microsoft/qlib/blob/main/docs/component/workflow.rst) — datasets, train/validation/test, experiment recorder, backtests.
- [Microsoft Qlib: point-in-time database](https://github.com/microsoft/qlib/blob/main/docs/index.rst) — PIT als afzonderlijk dataonderdeel.
- [QuantConnect LEAN: engine](https://www.quantconnect.com/docs/v2/writing-algorithms/key-concepts/algorithm-engine) — event-time frontier en event-driven simulatie.
- [QuantConnect LEAN: reality modeling](https://www.quantconnect.com/docs/v2/writing-algorithms/reality-modeling/key-concepts) — fees, fills, slippage, capacity, brokerage.
- [TradingAgents: repository](https://github.com/TauricResearch/TradingAgents) — multi-agent analyse en historische beslisdatumcontroles.

## Beoordelingsregels

Status is **GEDEELTELIJK** als er aantoonbare onderzoeksmodules bestaan maar geen onafhankelijke end-to-end resultaten zijn; **NIET AANGETOOND** betekent niet dat er geen code is. Geen fictieve numerieke scores.

| Discipline | Externe referentie | DIPSAUS-status (voorlopig) | Eerstvolgende bewijsopdracht |
| --- | --- | --- | --- |
| Point-in-time bronbeschikbaarheid | Qlib PIT, TradingAgents date guards | GEDEELTELIJK: SEC-acceptatie, accession, chronology, private-to-public gates; historische publieke verspreiding niet bewezen | Originele SEC bytes en onafhankelijk tijdstempel van publieke beschikbaarheid, vóór kandidaatbesluit |
| Reproduceerbare experimenten | Qlib experiment recorder | GEDEELTELIJK: dossier-hashes, CI, onderzoeksartefacten | Echte bevroren dataset, commit, config, bronversies, run-ID en herberekende uitkomsten in één manifest |
| Event-time / lookahead bescherming | LEAN time frontier | GEDEELTELIJK: registratie- en timestampcontroles | Replay waarin alle signalen uitsluitend vóór besluit beschikbare snapshots kunnen lezen |
| Realistische uitvoering | LEAN fee/fill/slippage models | GEDEELTELIJK: kosten- en entry-nadeelscenario's | DEGIRO-specifieke handelsbaarheid, valuta, spread, liquiditeit, partial fills en kosten op echte transacties |
| Survivorship / corporate actions | LEAN universe and adjustments | NIET AANGETOOND | Historische universa incl. delistings, splits, dividenden en symboolwijzigingen |
| Kapitaal- en portefeuillereconstructie | LEAN portfolio engine | GEDEELTELIJK: €50k, max. 6 posities, tranche-onderzoek | Tijdgestuurde cash ledger, overlap, geblokkeerd kapitaal, opportunity cost, reconciliatie |
| Onafhankelijke validatie | Qlib train/valid/test | GEDEELTELIJK: OOS/walk-forward onderzoek | Afgesloten OOS-cohorten met betrouwbaarheidsintervallen en benchmarks |
| AI-analisten / tegenspraak | TradingAgents | NIET AANGETOOND als onafhankelijke bewezen meerwaarde | Pas ná baseline: geblindeerde vergelijking met en zonder agentanalyse |

## Beslisvolgorde

1. **Bewijs boven architectuur:** minimaal één echte SEC complete submission als onveranderde bytes vastleggen, URL/sha256/ontvangsttijd registreren; expliciet onderscheid tussen ophaaltijd, acceptatie en historische publieke beschikbaarheid.
2. **Echte kandidaat koppelen:** historische registratie, beslissing en relevante marktdata; afwijzen bij ontbrekend point-in-time bewijs.
3. **Professionele simulatie:** event-driven replay met handelsbaarheid bij DEGIRO, liquiditeit, spreads, valuta, kosten en kapitaalbeslag. Geen automatische orders.
4. **Onafhankelijk beoordelen:** vaste baseline, OOS-periodes, kwartaalstresstests, symbol-out tests, opportunity cost en robuustheidsanalyse.
5. **Pas daarna AI-beslissingslaag:** multi-agent debat als gecontroleerd experiment; alleen integreren bij meetbare OOS-verbetering.

## Vaste randvoorwaarden

€50.000 onderzoeksportefeuille; maximaal zes posities; typische tranche €3.500; herstel-swing 5–15 handelsdagen; handmatige beslissingen; geen stoploss of stoplimiet; geen automatische orders. Geen wijzigingen aan main, operationele scanner of private sleutels.

## Acceptatiecriteria

Een onderdeel krijgt pas status **AANGETOOND** als de bijbehorende bewijsopdracht is uitgevoerd met echte relevante gegevens, reproduceerbare run, onafhankelijk controleerbare uitkomst en expliciet geregistreerde beperkingen. Groene CI op synthetische tests is noodzakelijk voor codekwaliteit maar onvoldoende voor bewezen handelsvoordeel.
