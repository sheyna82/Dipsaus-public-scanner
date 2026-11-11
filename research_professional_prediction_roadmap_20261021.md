# DIPSAUS: professionele voorspellingsresearch — bronnen en roadmap (21 oktober 2026)

## Kernconclusie
Geen extra ongetoetste indicatoren in productie. Bouw drie afzonderlijke voorspellingsproblemen: herstel in 3/5/10 handelsdagen, tussentijdse downside en earnings-eventrisico. Kansscores alleen na out-of-sample kalibratie. Gratis software betekent niet automatisch gratis marktdata.

## Professionele onderzoeksarchitectuur
1. Hypothese + expliciete uitkomstdefinitie; referentie (buy-and-hold, eenvoudige momentumregel, willekeurig signaal).
2. Point-in-time data, corporate actions, delistings, publicatietijd, tijdzones, datarechten.
3. Walk-forward; purge overlappende labelhorizons; embargo; geen tuning op testresultaten.
4. Modelvergelijking: eerst eenvoudige logistische regressie en regelgebaseerde score, dan pas complexere modellen.
5. Metingen: precisie/recall per drempel, Brier score, kalibratie, coverage, maximum adverse excursion, 3/5/10D returns, transactiekosten, sector- en regime-uitsplitsingen.
6. Realistische order-fill/slippage; niet aannemen dat limietprijs aanraken = uitvoerbare order.
7. Paper-forward, driftbewaking, meldingsbudget en handmatige toestemming vóór productie.

## Open-source referenties
- Microsoft Qlib (MIT): https://github.com/microsoft/qlib
- QuantConnect LEAN (Apache-2.0): https://github.com/QuantConnect/Lean
- Freqtrade (GPLv3, crypto): https://github.com/freqtrade/freqtrade
- vectorbt community (Apache 2.0 met Commons Clause; PRO betaald): https://github.com/polakowo/vectorbt
- Open-source projectcatalogus (niet elk project onafhankelijk gecontroleerd): https://github.com/WallStreetPete/awesome-open-source-trading
- QuantConnect fill/slippage: https://www.quantconnect.com/docs/v2/writing-algorithms/reality-modeling/key-concepts
- Walk-forward/purged CV uitleg: https://openalgo.in/quant/walkforward-purged-cv

## Academische earnings-research
- PEAD review: https://doi.org/10.1016/j.jbef.2020.100446
- Analyst responsiveness: https://www.sciencedirect.com/science/article/pii/S0165410108000220
- Options orderflow before earnings: https://www.sciencedirect.com/science/article/pii/S2214845026001286

## Gratis officiële databronnen
- SEC EDGAR: https://www.sec.gov/about/developer-resources — filings/XBRL; fair-access en historische publicatietijd verifiëren.
- EIA API: https://www.eia.gov/developer/ — gratis, registratie/API-sleutel vereist voor API; geen betaalde afhankelijkheid. Gas storage release: donderdag 10:30 ET, afwijkingen rond feestdagen.
- FRED/ALFRED: https://fred.stlouisfed.org/docs/api/fred/ — historische macro-revisies via vintage dates; API-sleutel kan vereist zijn.
- CFTC COT: https://www.cftc.gov/MarketReports/CommitmentsofTraders/ReleaseSchedule/index.htm — meestal vrijdag 15:30 ET over voorgaande dinsdag; wekelijkse vertraging in backtests respecteren.

## Onderzoeksprioriteit
P0: gratis/licentie-geschikte koersdata EU+VS en point-in-time timestamps aantonen.
P1: baseline recovery model + as-of audits + walk-forward en purging.
P2: realistische limit-order fills, MAE, kosten, kalibratie.
P3: earnings- en sectorspecifieke modules (EXE gas/EIA) met aparte score voor onzekerheid en richting.
P4: paper-forward en alertkwaliteit voordat iets live gaat.

## Stopcriteria
Geen productie als datarechten onduidelijk, labels lekken, te weinig out-of-sample waarnemingen, kalibratie faalt, performance verdwijnt na kosten of model slechter presteert dan eenvoudige baseline.

Geen code uit projecten overgenomen, geen live scanner/orders gewijzigd, geen betaalde data aangesloten.
