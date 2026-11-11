# DIPSAUS — externe scannercomponenten: onderzoeksregister

Status: verkenning op 23 oktober 2026. **Nog geen broncode overgenomen.** Dit register onderscheidt vindbaarheid van daadwerkelijke code-audit. Repositories zijn zoekresultaten; functionaliteit, onderhoud, licentie en prestaties moeten per bron nog afzonderlijk worden geverifieerd.

| Externe bron | Onderzoekbare bouwsteen | Potentieel nut DIPSAUS | Verificatie |
|---|---|---|---|
| [mementum/backtrader](https://github.com/mementum/backtrader) | Event-driven backtesting, order-/kostenmodellering | Realistischer historische simulaties en frictie | Code, licentie, aannames en testkwaliteit nog inspecteren |
| [kernc/backtesting.py](https://github.com/kernc/backtesting.py) | Strategiebacktests en evaluatie | Tweede, onafhankelijke testimplementatie als controlegroep | Nog inspecteren |
| [lit26/Stock_Screener](https://github.com/lit26/Stock_Screener) | Screening-architectuur | Kandidatenselectie en indicatorfilters | Nog inspecteren |
| [AdamGetbags/breakoutScanner](https://github.com/AdamGetbags/breakoutScanner) | Breakout-signalen | Vergelijking vroege uitbraak versus herstel | Nog inspecteren |
| [cbyhre/Stock-News-Scanner](https://github.com/cbyhre/Stock-News-Scanner) | Nieuwssignalen | Context zonder onnodige meldingen | Nog inspecteren |
| [bilalaslam28/Automated-VSA-Pre-Market-Stock-Scanner](https://github.com/bilalaslam28/Automated-VSA-Pre-Market-Stock-Scanner) | Premarket en volume/spread-analyse | Vroegtijdige waarschuwingen en volumebevestiging | Nog inspecteren |

## Vergelijkingsrubriek per bouwsteen

1. Wat doet de implementatie daadwerkelijk? Lees code en tests, niet alleen README of claims.
2. Is het signaal causaal? Data release-tijd, look-ahead, survivorship en herzieningen.
3. Wat is de gemeten meerwaarde tegenover eenvoudige basisregels op onafhankelijk holdoutmateriaal?
4. Hoe gaat het om met foutpositieven, vertraging, transactiekosten en verschillende markten?
5. Kan het onderdeel los worden hergebruikt, of alleen als concept worden herbouwd? Controleer licentie en afhankelijkheden.
6. Past het bij DIPSAUS: herstel-swing over dagen/weken, weinig ruis, risico-informatie en limietorders zonder verplichte stoploss?
7. Kan de verbetering geïsoleerd op de onderzoeksbranch worden getest zonder live alerts of privégegevens?

## Prioriteiten

**P1:** onafhankelijke walk-forward-evaluatie, frictie, dataprovenance en leakage-audit.  
**P2:** herstel versus breakout; volume- en volatiliteitsbevestiging; regimefilters.  
**P3:** event/nieuwscontext, premarket-waarschuwingen en adaptieve alertdrempels.

## Beslisregel

Hergebruik van bestaande broncode heeft expliciet de voorkeur boven onnodig opnieuw bouwen wanneer de code veilig, betrouwbaar, kosteloos beschikbaar en juridisch herbruikbaar is. MIT/BSD/Apache-licenties vragen behoud van toepasselijke kennisgevingen; GPL/AGPL vereisen extra beoordeling van verplichtingen; zonder licentie niet kopiëren. Beoordeel per component directe overname, aangepaste integratie of zelfstandige implementatie. Niet overnemen op basis van populariteit, marketing of een aantrekkelijke backtest. Eerst component isoleren, baseline formuleren, falsificatietest bouwen, daarna alleen bij aantoonbare meerwaarde integreren. Geen automatische handel; geen wijzigingen aan de productiebranch zonder expliciete toestemming.

## Eerste broninspectie: backtest-uitvoering (23 oktober 2026)

**Backtrader**: README beschrijft configureerbare commissies, slippage, volume filling, limit-orders, meerdere tijdframes en een expliciete *cheat-on-close/open*-optie. Voor DIPSAUS zijn vooral realistische fill-aannames en het vermijden van uitvoering tegen een nog onbekende slotkoers relevant. Project meldt GPL-3.0; code niet kopiëren zonder licentiebeoordeling. Bron: https://github.com/mementum/backtrader

**Backtesting.py**: publieke API en implementatie beschrijven spread, vaste/procentuele commissies, standaarduitvoering van marktorders op de volgende candle-open, optionele trade_on_close en limietorders. Bij DIPSAUS moeten de hypothetische limietverkopen en gemiste fills expliciet worden meegenomen, ook als de scanner zelf geen orders plaatst. Project meldt AGPL-3.0; code niet kopiëren zonder licentiebeoordeling. Bronnen: https://kernc.github.io/backtesting.py/doc/backtesting/backtesting.html en https://github.com/kernc/backtesting.py/blob/master/backtesting/backtesting.py

**Besluit voor een geïsoleerde DIPSAUS-proef:** bouw eerst een eigen, kleine execution-assumption-audit die scenario's vergelijkt (volgende opening versus slotkoers, spread, kosten, niet-uitgevoerde limietorders) op synthetische OHLCV. Dit is **niet** hetzelfde als een gevalideerde strategiebacktest en bewijst geen voorspellende waarde. Externe code mag worden geïntegreerd na controle van veiligheid, licentie, afhankelijkheden en aantoonbare meerwaarde.

**Open punten:** testdekking van de twee upstream-projecten, actuele onderhoudsstatus, exacte order-fill-semantiek bij gaps en gedeeltelijke uitvoering, licentieadvies en realistische brokerdata. De vier overige projecten zijn nog niet inhoudelijk geaudit.

## Licentie- en architectuurcontrole (23 oktober 2026)

| Bron | Rechtstreeks gecontroleerd | Hergebruikadvies |
|---|---|---|
| lit26/Stock_Screener | LICENSE = MIT; README beschrijft Django + React; requirements.txt pint Django 3.2, pandas 1.2.3, yfinance 0.1.63, finvizfinance 0.11.1, ta 0.7.0 en DRF 3.12.4 | **Niet de oude stack integraal overnemen**; isoleer een specifieke screeningfunctie en test actuele dependencies, datarechten en veiligheid |
| cbyhre/Stock-News-Scanner | LICENSE = MIT; README noemt het scrapen van StockTitan-headlines van afgelopen 30 minuten | Alleen ticker-/headline-extractie na broncode-audit overwegen; **scrapingvoorwaarden en tijdstempelbetrouwbaarheid** apart toetsen |
| mementum/backtrader | LICENSE = GPL-3.0 | Eerst als referentie of afzonderlijk onderzoeksinstrument; compatibiliteit met distributie DIPSAUS beoordelen |
| kernc/backtesting.py | LICENSE.md = AGPL-3.0 | Eerst als referentie of afzonderlijk onderzoeksinstrument; compatibiliteit met distributie DIPSAUS beoordelen |
| AdamGetbags/breakoutScanner | README aanwezig; geen LICENSE of LICENSE.md aangetroffen op onderzochte paden | Geen code kopiëren zonder rechtenvaststelling |
| bilalaslam28/Automated-VSA-Pre-Market-Stock-Scanner | README aanwezig; geen LICENSE of LICENSE.md aangetroffen op onderzochte paden | Geen code kopiëren zonder rechtenvaststelling |

**Conclusie:** een MIT-licentie maakt hergebruik juridisch makkelijker, maar zegt niets over veiligheid, databronrechten, onderhoud of voorspellende waarde. Voorlopig geen externe code geïntegreerd. Eerst een specifieke MIT-component en diens tests en afhankelijkheden volledig inspecteren.

## Code-audit: lit26/Stock_Screener (23 oktober 2026)

Bestanden direct gelezen: `api/screener.py`, `api/cache.py`, `api/technical.py` (upstream MIT; copyright Tianning Li, 2021).

- `api/screener.py`: valideert filterlabels tegen `finvizfinance.util.util_dict` en construeert een Finviz-URL. Het parseert vervolgens vaste HTML-tabelindices (17/18) en gebruikt `DataFrame.append`. **Niet rechtstreeks integreren:** kwetsbaar voor sitewijzigingen, versiebreuk en externe scraping-/gebruiksvoorwaarden; ook geen point-in-time databewijs.
- `api/cache.py`: eenvoudige ticker/interval/periode-cache; een andere cache gebruikt `datetime.now()` en een TTL van 15 minuten. **Wel nuttig als architectuuridee**, maar bij DIPSAUS moet de cache key ook provider, as-of tijd, markt, adjustment en data-versie omvatten; stale data mag geen live alert opleveren.
- `api/technical.py`: berekent EMA, Bollinger Bands, MACD, RSI en stochastic via de `ta`-bibliotheek, voornamelijk voor grafiekweergave. **Interessant als indicator-controlegroep**, niet als zelfstandig bewezen herstelmodel; vermijd afronding vóór scoreberekening.
- De MIT-licentie staat hergebruik met licentiebehoud toe, maar geeft geen toestemming voor het scrapen van Finviz of toegang tot marktdatabronnen.

**Besluit:** geen volledige stack of Finviz-scraper overnemen. Eerst een eigen, offline cache-key- en freshness-gate onderzoeken; pas na controle van de concrete bestaande DIPSAUS-cache integreren. Technische indicatoren vergelijken met bestaande signalen via causale holdout. Er is nog geen externe code gekopieerd.
